from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin, require_authenticated_user
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUserResponse, TokenResponse
from app.schemas.common import SimpleMessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    auth_service = AuthService(UserRepository(db))
    user = auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )
    access_token, expires_in = auth_service.create_access_token_for_user(user)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Retornar usuário autenticado",
)
def read_current_user(
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@router.get(
    "/admin-check",
    response_model=SimpleMessageResponse,
    include_in_schema=False,
)
def admin_check(
    current_user: Annotated[User, Depends(require_admin)],
) -> SimpleMessageResponse:
    return SimpleMessageResponse(message="Acesso de administrador concedido.")
