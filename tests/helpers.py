from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableException
from app.core.security import hash_password
from app.db.models.user import User
from app.db.models.vehicle import Vehicle
from app.enums.role import UserRole
from app.utils.datetime import utc_now
from app.utils.money import quantize_exchange_rate, quantize_money
from app.utils.plate import validate_and_normalize_plate

TEST_ADMIN_CREDENTIALS = {
    "username": "admin",
    "email": "admin@test.local",
    "password": "Admin123!",
    "role": UserRole.ADMIN,
}

TEST_USER_CREDENTIALS = {
    "username": "user",
    "email": "user@test.local",
    "password": "User123!",
    "role": UserRole.USER,
}


class FixedExchangeRateService:
    def __init__(self, rate: Decimal = Decimal("5.0000")) -> None:
        normalized_rate = quantize_exchange_rate(rate)
        if normalized_rate <= 0:
            raise ValueError("A cotação precisa ser positiva.")
        self.rate = normalized_rate

    def get_usd_brl_rate(self) -> Decimal:
        return self.rate

    def convert_brl_to_usd(self, amount_brl: Decimal) -> Decimal:
        return quantize_money(amount_brl / self.rate)


class FailingExchangeRateService:
    def get_usd_brl_rate(self) -> Decimal:
        raise ServiceUnavailableException(
            message="Não foi possível obter a cotação USD/BRL nos provedores externos.",
            code="EXCHANGE_RATE_UNAVAILABLE",
        )

    def convert_brl_to_usd(self, amount_brl: Decimal) -> Decimal:
        raise ServiceUnavailableException(
            message="Não foi possível obter a cotação USD/BRL nos provedores externos.",
            code="EXCHANGE_RATE_UNAVAILABLE",
        )


def create_user(
    session: Session,
    *,
    username: str,
    email: str,
    password: str,
    role: UserRole,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_vehicle(
    session: Session,
    *,
    brand: str = "Toyota",
    model: str = "Corolla",
    year: int = 2022,
    color: str = "Prata",
    plate: str = "ABC1D23",
    price_usd: Decimal = Decimal("25000.00"),
    is_active: bool = True,
) -> Vehicle:
    now = utc_now()
    vehicle = Vehicle(
        brand=brand,
        model=model,
        year=year,
        color=color,
        plate=validate_and_normalize_plate(plate),
        price_usd=quantize_money(price_usd),
        is_active=is_active,
        created_at=now,
        updated_at=now,
        deleted_at=None if is_active else now,
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return vehicle


def get_access_token(client: TestClient, *, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
