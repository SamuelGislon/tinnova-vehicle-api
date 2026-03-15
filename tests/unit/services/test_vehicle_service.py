from decimal import Decimal

import pytest

from app.core.exceptions import BadRequestException, ConflictException
from app.db.models.vehicle import Vehicle
from app.schemas.vehicle import (
    SortOrder,
    VehicleCreate,
    VehicleListFilters,
    VehiclePatch,
    VehiclePut,
    VehicleSortField,
)
from app.services.vehicle_service import VehicleService
from app.utils.datetime import utc_now
from app.utils.plate import normalize_plate
from tests.helpers import FixedExchangeRateService

pytestmark = pytest.mark.unit


class InMemoryVehicleRepository:
    def __init__(self) -> None:
        self.items: dict[int, Vehicle] = {}
        self.next_id = 1

    def create(self, vehicle: Vehicle) -> Vehicle:
        now = utc_now()
        vehicle.id = self.next_id
        self.next_id += 1
        vehicle.created_at = now
        vehicle.updated_at = now
        vehicle.deleted_at = None
        self.items[vehicle.id] = vehicle
        return vehicle

    def get_by_id(self, vehicle_id: int, *, include_inactive: bool = False) -> Vehicle | None:
        vehicle = self.items.get(vehicle_id)
        if vehicle is None:
            return None
        if not include_inactive and not vehicle.is_active:
            return None
        return vehicle

    def get_by_plate(self, plate: str, *, include_inactive: bool = True) -> Vehicle | None:
        normalized = normalize_plate(plate)
        for vehicle in self.items.values():
            if vehicle.plate != normalized:
                continue
            if include_inactive or vehicle.is_active:
                return vehicle
        return None

    def list_vehicles(self, filters: VehicleListFilters):
        items = [vehicle for vehicle in self.items.values() if vehicle.is_active]

        if filters.brand:
            items = [item for item in items if filters.brand.lower() in item.brand.lower()]
        if filters.year is not None:
            items = [item for item in items if item.year == filters.year]
        if filters.color:
            items = [item for item in items if filters.color.lower() in item.color.lower()]
        if filters.plate:
            items = [item for item in items if item.plate == filters.plate]
        if filters.min_price is not None:
            items = [item for item in items if item.price_usd >= filters.min_price]
        if filters.max_price is not None:
            items = [item for item in items if item.price_usd <= filters.max_price]

        sort_attr = {
            VehicleSortField.CREATED_AT: "created_at",
            VehicleSortField.UPDATED_AT: "updated_at",
            VehicleSortField.BRAND: "brand",
            VehicleSortField.YEAR: "year",
            VehicleSortField.PRICE_USD: "price_usd",
        }[filters.sort_by]

        reverse = filters.sort_order == SortOrder.DESC
        items = sorted(items, key=lambda item: getattr(item, sort_attr), reverse=reverse)

        total = len(items)
        start = (filters.page - 1) * filters.page_size
        end = start + filters.page_size

        return items[start:end], total

    def update(self, vehicle: Vehicle) -> Vehicle:
        vehicle.updated_at = utc_now()
        self.items[vehicle.id] = vehicle
        return vehicle

    def soft_delete(self, vehicle: Vehicle) -> Vehicle:
        vehicle.is_active = False
        vehicle.deleted_at = utc_now()
        vehicle.updated_at = utc_now()
        self.items[vehicle.id] = vehicle
        return vehicle


def make_service() -> tuple[VehicleService, InMemoryVehicleRepository]:
    repository = InMemoryVehicleRepository()
    exchange_service = FixedExchangeRateService(rate=Decimal("5.0000"))
    service = VehicleService(
        vehicle_repository=repository,
        exchange_rate_service=exchange_service,
    )
    return service, repository


def create_seed_vehicle(repository: InMemoryVehicleRepository) -> Vehicle:
    vehicle = Vehicle(
        brand="Toyota",
        model="Corolla",
        year=2022,
        color="Prata",
        plate="ABC1D23",
        price_usd=Decimal("25000.00"),
        is_active=True,
    )
    return repository.create(vehicle)


def test_create_vehicle_converts_brl_to_usd() -> None:
    service, _repository = make_service()

    created = service.create_vehicle(
        VehicleCreate(
            brand="Toyota",
            model="Corolla",
            year=2022,
            color="Prata",
            plate="ABC-1D23",
            price_brl=Decimal("125000.00"),
        )
    )

    assert created.plate == "ABC1D23"
    assert created.price_usd == Decimal("25000.00")


def test_create_vehicle_rejects_duplicate_plate() -> None:
    service, repository = make_service()
    create_seed_vehicle(repository)

    with pytest.raises(ConflictException, match="Já existe um veículo cadastrado com esta placa."):
        service.create_vehicle(
            VehicleCreate(
                brand="Honda",
                model="Civic",
                year=2021,
                color="Cinza",
                plate="abc-1d23",
                price_brl=Decimal("100000.00"),
            )
        )


def test_patch_vehicle_rejects_empty_payload() -> None:
    service, repository = make_service()
    vehicle = create_seed_vehicle(repository)

    with pytest.raises(
        BadRequestException, match="Informe ao menos um campo para atualização parcial."
    ):
        service.patch_vehicle(vehicle.id, VehiclePatch())


def test_list_vehicles_rejects_invalid_price_range() -> None:
    service, _repository = make_service()

    with pytest.raises(BadRequestException, match="minPreco não pode ser maior"):
        service.list_vehicles(
            VehicleListFilters(
                min_price=Decimal("20000.00"),
                max_price=Decimal("10000.00"),
            )
        )


def test_put_vehicle_replaces_all_editable_fields() -> None:
    service, repository = make_service()
    vehicle = create_seed_vehicle(repository)

    updated = service.put_vehicle(
        vehicle.id,
        VehiclePut(
            brand="Honda",
            model="Civic",
            year=2023,
            color="Preto",
            plate="BRA2E19",
            price_brl=Decimal("150000.00"),
        ),
    )

    assert updated.brand == "Honda"
    assert updated.model == "Civic"
    assert updated.year == 2023
    assert updated.color == "Preto"
    assert updated.plate == "BRA2E19"
    assert updated.price_usd == Decimal("30000.00")


def test_patch_vehicle_updates_only_sent_fields() -> None:
    service, repository = make_service()
    vehicle = create_seed_vehicle(repository)

    updated = service.patch_vehicle(
        vehicle.id,
        VehiclePatch(
            color="Preto",
            price_brl=Decimal("130000.00"),
        ),
    )

    assert updated.brand == "Toyota"
    assert updated.model == "Corolla"
    assert updated.color == "Preto"
    assert updated.price_usd == Decimal("26000.00")


def test_delete_vehicle_applies_soft_delete() -> None:
    service, repository = make_service()
    vehicle = create_seed_vehicle(repository)

    service.delete_vehicle(vehicle.id)

    deleted = repository.get_by_id(vehicle.id, include_inactive=True)
    assert deleted is not None
    assert deleted.is_active is False
    assert deleted.deleted_at is not None
