from datetime import UTC, datetime
from decimal import Decimal

from app.db.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate
from app.services.exchange_rate_service import ExchangeRateService
from app.services.vehicle_service import VehicleService
from app.utils.plate import normalize_plate


class FakeExchangeRateClient:
    def __init__(self, primary_rate: Decimal) -> None:
        self.primary_rate = primary_rate
        self.primary_calls = 0
        self.fallback_calls = 0

    def fetch_primary_usd_brl_rate(self) -> Decimal:
        self.primary_calls += 1
        return self.primary_rate

    def fetch_fallback_usd_brl_rate(self) -> Decimal:
        self.fallback_calls += 1
        raise AssertionError("Fallback não deveria ser chamado neste teste.")


class FakeCacheClient:
    def __init__(self, cached_rate: Decimal | None = None) -> None:
        self.cached_rate = cached_rate
        self.last_ttl: int | None = None

    def get_usd_brl_rate(self) -> Decimal | None:
        return self.cached_rate

    def set_usd_brl_rate(self, rate: Decimal, ttl_seconds: int) -> None:
        self.cached_rate = rate
        self.last_ttl = ttl_seconds


class InMemoryVehicleRepository:
    def __init__(self) -> None:
        self.items: dict[int, Vehicle] = {}
        self.next_id = 1

    def create(self, vehicle: Vehicle) -> Vehicle:
        vehicle.id = self.next_id
        self.next_id += 1

        now = datetime.now(UTC)
        vehicle.created_at = now
        vehicle.updated_at = now
        vehicle.deleted_at = None

        self.items[vehicle.id] = vehicle
        return vehicle

    def get_by_plate(self, plate: str, *, include_inactive: bool = True) -> Vehicle | None:
        normalized = normalize_plate(plate)

        for vehicle in self.items.values():
            if vehicle.plate != normalized:
                continue
            if include_inactive or vehicle.is_active:
                return vehicle

        return None


def test_vehicle_service_continues_working_with_real_exchange_rate_service() -> None:
    repository = InMemoryVehicleRepository()
    cache = FakeCacheClient()
    exchange_rate_client = FakeExchangeRateClient(primary_rate=Decimal("5.0000"))
    exchange_rate_service = ExchangeRateService(
        exchange_rate_client=exchange_rate_client,
        cache_client=cache,
        ttl_seconds=300,
    )

    service = VehicleService(
        vehicle_repository=repository,
        exchange_rate_service=exchange_rate_service,
    )

    payload = VehicleCreate(
        brand="Toyota",
        model="Corolla",
        year=2022,
        color="Prata",
        plate="ABC-1D23",
        price_brl=Decimal("125000.00"),
    )

    created = service.create_vehicle(payload)

    assert created.plate == "ABC1D23"
    assert created.price_usd == Decimal("25000.00")
    assert exchange_rate_client.primary_calls == 1
    assert exchange_rate_client.fallback_calls == 0
    assert cache.cached_rate == Decimal("5.0000")
