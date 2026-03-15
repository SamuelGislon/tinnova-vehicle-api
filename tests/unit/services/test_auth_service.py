import pytest

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token, hash_password
from app.db.models.user import User
from app.enums.role import UserRole
from app.services.auth_service import AuthService

pytestmark = pytest.mark.unit


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user

    def get_by_username(self, username: str) -> User | None:
        return self.user


def build_user(*, password: str, is_active: bool = True) -> User:
    user = User(
        id=1,
        username="admin",
        email="admin@test.local",
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=is_active,
    )
    return user


def test_authenticate_user_with_valid_credentials() -> None:
    user = build_user(password="Admin123!")
    service = AuthService(FakeUserRepository(user))

    authenticated = service.authenticate_user(
        username="admin",
        password="Admin123!",
    )

    assert authenticated.username == "admin"
    assert authenticated.role == UserRole.ADMIN


def test_authenticate_user_with_invalid_password_raises_401() -> None:
    user = build_user(password="Admin123!")
    service = AuthService(FakeUserRepository(user))

    with pytest.raises(UnauthorizedException, match="Usuário ou senha inválidos."):
        service.authenticate_user(
            username="admin",
            password="WrongPassword",
        )


def test_authenticate_user_with_inactive_user_raises_401() -> None:
    user = build_user(password="Admin123!", is_active=False)
    service = AuthService(FakeUserRepository(user))

    with pytest.raises(UnauthorizedException, match="Usuário ou senha inválidos."):
        service.authenticate_user(
            username="admin",
            password="Admin123!",
        )


def test_create_access_token_for_user_returns_token_and_expiration() -> None:
    user = build_user(password="Admin123!")
    service = AuthService(FakeUserRepository(user))

    token, expires_in = service.create_access_token_for_user(user)
    payload = decode_access_token(token)

    assert isinstance(token, str)
    assert expires_in > 0
    assert payload["sub"] == "1"
    assert payload["role"] == "ADMIN"
