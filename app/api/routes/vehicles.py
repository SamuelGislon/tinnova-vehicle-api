from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.dependencies.auth import require_admin, require_authenticated_user
from app.api.dependencies.services import get_vehicle_service
from app.db.models.user import User
from app.schemas.vehicle import (
    PaginatedVehicleResponse,
    SortOrder,
    VehicleCreate,
    VehicleListFilters,
    VehiclePatch,
    VehiclePut,
    VehicleResponse,
    VehicleSortField,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/veiculos", tags=["Vehicles"])


def get_vehicle_filters(
    brand: str | None = Query(default=None),
    marca: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1900),
    ano: int | None = Query(default=None, ge=1900),
    color: str | None = Query(default=None),
    cor: str | None = Query(default=None),
    plate: str | None = Query(default=None),
    placa: str | None = Query(default=None),
    min_preco: Decimal | None = Query(
        default=None,
        alias="minPreco",
        gt=0,
        max_digits=12,
        decimal_places=2,
    ),
    max_preco: Decimal | None = Query(
        default=None,
        alias="maxPreco",
        gt=0,
        max_digits=12,
        decimal_places=2,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: VehicleSortField = Query(default=VehicleSortField.CREATED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> VehicleListFilters:
    try:
        return VehicleListFilters(
            brand=brand or marca,
            year=year or ano,
            color=color or cor,
            plate=plate or placa,
            min_price=min_preco,
            max_price=max_preco,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get(
    "",
    response_model=PaginatedVehicleResponse,
    summary="Listar veículos com filtros, paginação e ordenação",
)
def list_vehicles(
    filters: Annotated[VehicleListFilters, Depends(get_vehicle_filters)],
    current_user: Annotated[User, Depends(require_authenticated_user)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> PaginatedVehicleResponse:
    _ = current_user
    return vehicle_service.list_vehicles(filters)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Detalhar veículo por ID",
)
def get_vehicle_by_id(
    vehicle_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> VehicleResponse:
    _ = current_user
    return vehicle_service.get_vehicle_by_id(vehicle_id)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar veículo",
)
def create_vehicle(
    payload: VehicleCreate,
    current_user: Annotated[User, Depends(require_admin)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> VehicleResponse:
    _ = current_user
    return vehicle_service.create_vehicle(payload)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Atualizar veículo completamente",
)
def put_vehicle(
    vehicle_id: int,
    payload: VehiclePut,
    current_user: Annotated[User, Depends(require_admin)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> VehicleResponse:
    _ = current_user
    return vehicle_service.put_vehicle(vehicle_id, payload)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Atualizar veículo parcialmente",
)
def patch_vehicle(
    vehicle_id: int,
    payload: VehiclePatch,
    current_user: Annotated[User, Depends(require_admin)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> VehicleResponse:
    _ = current_user
    return vehicle_service.patch_vehicle(vehicle_id, payload)


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover veículo logicamente",
)
def delete_vehicle(
    vehicle_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    vehicle_service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> Response:
    _ = current_user
    vehicle_service.delete_vehicle(vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
