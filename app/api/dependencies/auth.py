from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.enums.role import UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise UnauthorizedException(message="Token inválido ou expirado.") from exc

    subject = payload.get("sub")
    if subject is None:
        raise UnauthorizedException(message="Token inválido ou expirado.")

    try:
        user_id = int(subject)
    except ValueError as exc:
        raise UnauthorizedException(message="Token inválido ou expirado.") from exc

    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None or not user.is_active:
        raise UnauthorizedException(message="Token inválido ou expirado.")

    return user


def require_authenticated_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(message="Acesso restrito a administradores.")

    return current_user
