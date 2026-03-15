from collections.abc import Sequence

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.db.models.vehicle import Vehicle
from app.schemas.vehicle import SortOrder, VehicleListFilters, VehicleSortField
from app.utils.datetime import utc_now
from app.utils.plate import normalize_plate

SORT_FIELD_MAP = {
    VehicleSortField.CREATED_AT: Vehicle.created_at,
    VehicleSortField.UPDATED_AT: Vehicle.updated_at,
    VehicleSortField.BRAND: Vehicle.brand,
    VehicleSortField.YEAR: Vehicle.year,
    VehicleSortField.PRICE_USD: Vehicle.price_usd,
}


class VehicleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_by_id(self, vehicle_id: int, *, include_inactive: bool = False) -> Vehicle | None:
        stmt = select(Vehicle).where(Vehicle.id == vehicle_id)

        if not include_inactive:
            stmt = stmt.where(Vehicle.is_active.is_(True))

        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_plate(
        self,
        plate: str,
        *,
        include_inactive: bool = True,
    ) -> Vehicle | None:
        normalized_plate = normalize_plate(plate)

        stmt = select(Vehicle).where(Vehicle.plate == normalized_plate)

        if not include_inactive:
            stmt = stmt.where(Vehicle.is_active.is_(True))

        return self.db.execute(stmt).scalar_one_or_none()

    def list_vehicles(self, filters: VehicleListFilters) -> tuple[Sequence[Vehicle], int]:
        stmt = select(Vehicle).where(Vehicle.is_active.is_(True))
        stmt = self._apply_filters(stmt, filters)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.execute(count_stmt).scalar_one()

        sort_column = SORT_FIELD_MAP[filters.sort_by]
        sort_expression = (
            sort_column.asc() if filters.sort_order == SortOrder.ASC else sort_column.desc()
        )

        stmt = (
            stmt.order_by(sort_expression, Vehicle.id.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        items = self.db.execute(stmt).scalars().all()
        return items, total

    def update(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def soft_delete(self, vehicle: Vehicle) -> Vehicle:
        vehicle.is_active = False
        vehicle.deleted_at = utc_now()
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_brand_report_rows(self) -> list[tuple[str, int]]:
        total_label = func.count(Vehicle.id).label("total_active_vehicles")

        stmt = (
            select(Vehicle.brand, total_label)
            .where(Vehicle.is_active.is_(True))
            .group_by(Vehicle.brand)
            .order_by(desc(total_label), Vehicle.brand.asc())
        )

        return [(brand, total) for brand, total in self.db.execute(stmt).all()]

    def _apply_filters(
        self, stmt: Select[tuple[Vehicle]], filters: VehicleListFilters
    ) -> Select[tuple[Vehicle]]:
        if filters.brand:
            stmt = stmt.where(Vehicle.brand.ilike(f"%{filters.brand}%"))

        if filters.year is not None:
            stmt = stmt.where(Vehicle.year == filters.year)

        if filters.color:
            stmt = stmt.where(Vehicle.color.ilike(f"%{filters.color}%"))

        if filters.plate:
            stmt = stmt.where(Vehicle.plate == filters.plate)

        if filters.min_price is not None:
            stmt = stmt.where(Vehicle.price_usd >= filters.min_price)

        if filters.max_price is not None:
            stmt = stmt.where(Vehicle.price_usd <= filters.max_price)

        return stmt
