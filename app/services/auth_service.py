from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def authenticate_user(self, *, username: str, password: str) -> User:
        user = self.user_repository.get_by_username(username)

        if user is None or not user.is_active:
            raise UnauthorizedException(message="Usuário ou senha inválidos.")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException(message="Usuário ou senha inválidos.")

        return user

    def create_access_token_for_user(self, user: User) -> tuple[str, int]:
        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            expires_minutes=settings.access_token_expire_minutes,
        )
        expires_in = settings.access_token_expire_minutes * 60
        return token, expires_in
