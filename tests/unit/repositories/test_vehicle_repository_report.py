from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository


def create_test_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return session_local()


def test_get_brand_report_rows_groups_by_brand_and_excludes_inactive() -> None:
    session = create_test_session()

    session.add_all(
        [
            Vehicle(
                brand="Toyota",
                model="Corolla",
                year=2022,
                color="Prata",
                plate="AAA1A11",
                price_usd=Decimal("25000.00"),
                is_active=True,
            ),
            Vehicle(
                brand="Toyota",
                model="Yaris",
                year=2021,
                color="Branco",
                plate="AAA1A12",
                price_usd=Decimal("20000.00"),
                is_active=True,
            ),
            Vehicle(
                brand="Honda",
                model="Civic",
                year=2020,
                color="Cinza",
                plate="BBB1B11",
                price_usd=Decimal("21000.00"),
                is_active=True,
            ),
            Vehicle(
                brand="Ford",
                model="Ka",
                year=2019,
                color="Preto",
                plate="CCC1C11",
                price_usd=Decimal("10000.00"),
                is_active=False,
                deleted_at=datetime.now(UTC),
            ),
        ]
    )
    session.commit()

    repository = VehicleRepository(session)
    rows = repository.get_brand_report_rows()

    assert rows == [("Toyota", 2), ("Honda", 1)]


def test_get_brand_report_rows_returns_empty_list_when_database_is_empty() -> None:
    session = create_test_session()
    repository = VehicleRepository(session)

    rows = repository.get_brand_report_rows()

    assert rows == []
