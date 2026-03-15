from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import SortOrder, VehicleListFilters, VehicleSortField
from tests.helpers import create_vehicle

pytestmark = pytest.mark.unit


def test_list_vehicles_applies_combined_filters(db_session) -> None:
    repository = VehicleRepository(db_session)

    create_vehicle(
        db_session,
        brand="Toyota",
        model="Corolla",
        year=2022,
        color="Prata",
        plate="AAA1A11",
        price_usd=Decimal("25000.00"),
    )
    create_vehicle(
        db_session,
        brand="Toyota",
        model="Yaris",
        year=2021,
        color="Branco",
        plate="AAA1A12",
        price_usd=Decimal("18000.00"),
    )
    create_vehicle(
        db_session,
        brand="Honda",
        model="Civic",
        year=2022,
        color="Prata",
        plate="BBB1B11",
        price_usd=Decimal("26000.00"),
    )

    items, total = repository.list_vehicles(
        VehicleListFilters(
            brand="Toyota",
            year=2022,
            color="Prata",
            min_price=Decimal("20000.00"),
            max_price=Decimal("30000.00"),
            sort_by=VehicleSortField.PRICE_USD,
            sort_order=SortOrder.ASC,
        )
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].plate == "AAA1A11"


def test_get_by_plate_accepts_normalized_or_formatted_input(db_session) -> None:
    repository = VehicleRepository(db_session)
    create_vehicle(db_session, plate="ABC1D23")

    found = repository.get_by_plate("abc-1d23")

    assert found is not None
    assert found.plate == "ABC1D23"


def test_soft_delete_excludes_inactive_from_listing(db_session) -> None:
    repository = VehicleRepository(db_session)
    active = create_vehicle(db_session, plate="AAA1A11")
    inactive = create_vehicle(db_session, plate="BBB1B11")

    repository.soft_delete(inactive)

    items, total = repository.list_vehicles(VehicleListFilters())

    assert total == 1
    assert [item.id for item in items] == [active.id]


def test_get_brand_report_rows_counts_only_active(db_session) -> None:
    repository = VehicleRepository(db_session)

    create_vehicle(db_session, brand="Toyota", plate="AAA1A11")
    create_vehicle(db_session, brand="Toyota", plate="AAA1A12")
    create_vehicle(db_session, brand="Honda", plate="BBB1B11")
    create_vehicle(db_session, brand="Ford", plate="CCC1C11", is_active=False)

    rows = repository.get_brand_report_rows()

    assert rows == [("Toyota", 2), ("Honda", 1)]


def test_plate_uniqueness_is_enforced(db_session) -> None:
    create_vehicle(db_session, plate="ABC1D23")

    with pytest.raises(IntegrityError):
        create_vehicle(db_session, plate="abc-1d23")
