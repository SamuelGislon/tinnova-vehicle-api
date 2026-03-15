from math import ceil

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.db.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import (
    PaginatedVehicleResponse,
    VehicleCreate,
    VehicleListFilters,
    VehiclePatch,
    VehiclePut,
    VehicleResponse,
)
from app.services.exchange_rate_service import ExchangeRateServiceProtocol
from app.utils.plate import validate_and_normalize_plate


class VehicleService:
    def __init__(
        self,
        vehicle_repository: VehicleRepository,
        exchange_rate_service: ExchangeRateServiceProtocol,
    ) -> None:
        self.vehicle_repository = vehicle_repository
        self.exchange_rate_service = exchange_rate_service

    def create_vehicle(self, payload: VehicleCreate) -> VehicleResponse:
        normalized_plate = validate_and_normalize_plate(payload.plate)
        self._ensure_unique_plate(normalized_plate)

        price_usd = self.exchange_rate_service.convert_brl_to_usd(payload.price_brl)

        vehicle = Vehicle(
            brand=payload.brand,
            model=payload.model,
            year=payload.year,
            color=payload.color,
            plate=normalized_plate,
            price_usd=price_usd,
            is_active=True,
        )

        persisted = self._persist_create(vehicle)
        return VehicleResponse.model_validate(persisted)

    def get_vehicle_by_id(self, vehicle_id: int) -> VehicleResponse:
        vehicle = self._get_active_vehicle_or_404(vehicle_id)
        return VehicleResponse.model_validate(vehicle)

    def list_vehicles(self, filters: VehicleListFilters) -> PaginatedVehicleResponse:
        self._validate_price_range(filters)

        items, total = self.vehicle_repository.list_vehicles(filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return PaginatedVehicleResponse(
            items=[VehicleResponse.model_validate(item) for item in items],
            page=filters.page,
            page_size=filters.page_size,
            total=total,
            total_pages=total_pages,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )

    def put_vehicle(self, vehicle_id: int, payload: VehiclePut) -> VehicleResponse:
        vehicle = self._get_active_vehicle_or_404(vehicle_id)

        normalized_plate = validate_and_normalize_plate(payload.plate)
        self._ensure_unique_plate(normalized_plate, current_vehicle_id=vehicle.id)

        vehicle.brand = payload.brand
        vehicle.model = payload.model
        vehicle.year = payload.year
        vehicle.color = payload.color
        vehicle.plate = normalized_plate
        vehicle.price_usd = self.exchange_rate_service.convert_brl_to_usd(payload.price_brl)

        updated = self._persist_update(vehicle)
        return VehicleResponse.model_validate(updated)

    def patch_vehicle(self, vehicle_id: int, payload: VehiclePatch) -> VehicleResponse:
        vehicle = self._get_active_vehicle_or_404(vehicle_id)

        changes = payload.model_dump(exclude_unset=True)

        if not changes:
            raise BadRequestException(
                message="Informe ao menos um campo para atualização parcial.",
                code="EMPTY_PATCH_PAYLOAD",
            )

        if "brand" in changes:
            vehicle.brand = payload.brand  # type: ignore[assignment]

        if "model" in changes:
            vehicle.model = payload.model  # type: ignore[assignment]

        if "year" in changes:
            vehicle.year = payload.year  # type: ignore[assignment]

        if "color" in changes:
            vehicle.color = payload.color  # type: ignore[assignment]

        if "plate" in changes:
            normalized_plate = validate_and_normalize_plate(payload.plate or "")
            self._ensure_unique_plate(normalized_plate, current_vehicle_id=vehicle.id)
            vehicle.plate = normalized_plate

        if "price_brl" in changes:
            vehicle.price_usd = self.exchange_rate_service.convert_brl_to_usd(
                payload.price_brl  # type: ignore[arg-type]
            )

        updated = self._persist_update(vehicle)
        return VehicleResponse.model_validate(updated)

    def delete_vehicle(self, vehicle_id: int) -> None:
        vehicle = self._get_active_vehicle_or_404(vehicle_id)
        self.vehicle_repository.soft_delete(vehicle)

    def _get_active_vehicle_or_404(self, vehicle_id: int) -> Vehicle:
        vehicle = self.vehicle_repository.get_by_id(vehicle_id, include_inactive=False)

        if vehicle is None:
            raise NotFoundException(
                message="Veículo não encontrado.",
                code="VEHICLE_NOT_FOUND",
            )

        return vehicle

    def _ensure_unique_plate(
        self,
        plate: str,
        *,
        current_vehicle_id: int | None = None,
    ) -> None:
        existing_vehicle = self.vehicle_repository.get_by_plate(
            plate,
            include_inactive=True,
        )

        if existing_vehicle and existing_vehicle.id != current_vehicle_id:
            raise ConflictException(
                message="Já existe um veículo cadastrado com esta placa.",
                code="VEHICLE_ALREADY_EXISTS",
            )

    def _validate_price_range(self, filters: VehicleListFilters) -> None:
        if (
            filters.min_price is not None
            and filters.max_price is not None
            and filters.min_price > filters.max_price
        ):
            raise BadRequestException(
                message="O valor de minPreco não pode ser maior que maxPreco.",
                code="INVALID_PRICE_RANGE",
            )

    def _persist_create(self, vehicle: Vehicle) -> Vehicle:
        try:
            return self.vehicle_repository.create(vehicle)
        except IntegrityError as exc:
            self.vehicle_repository.db.rollback()
            raise self._translate_integrity_error(exc) from exc

    def _persist_update(self, vehicle: Vehicle) -> Vehicle:
        try:
            return self.vehicle_repository.update(vehicle)
        except IntegrityError as exc:
            self.vehicle_repository.db.rollback()
            raise self._translate_integrity_error(exc) from exc

    def _translate_integrity_error(self, exc: IntegrityError) -> Exception:
        message = str(exc.orig).lower()

        if "vehicles_plate_key" in message or "uq_vehicles_plate" in message:
            return ConflictException(
                message="Já existe um veículo cadastrado com esta placa.",
                code="VEHICLE_ALREADY_EXISTS",
            )

        return BadRequestException(
            message="Não foi possível persistir os dados do veículo.",
            code="VEHICLE_PERSISTENCE_ERROR",
        )
