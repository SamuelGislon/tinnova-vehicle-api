import logging
from collections.abc import Mapping
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.request_id import REQUEST_ID_HEADER, get_request_id
from app.schemas.error import ErrorContent, ErrorResponse, ValidationErrorDetail

logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)

    payload = ErrorResponse(
        error=ErrorContent(
            code=code,
            message=message,
            details=details,
            path=request.url.path,
            method=request.method,
            timestamp=datetime.now(UTC),
            request_id=request_id,
        )
    )

    response_headers = {REQUEST_ID_HEADER: request_id}
    if headers:
        response_headers.update(dict(headers))

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload),
        headers=response_headers,
    )


def _map_http_exception(exc: StarletteHTTPException) -> tuple[str, str]:
    if exc.status_code == 400:
        return "BAD_REQUEST", "Requisição inválida."
    if exc.status_code == 401:
        return "UNAUTHORIZED", "Não autenticado."
    if exc.status_code == 403:
        return "FORBIDDEN", "Acesso negado."
    if exc.status_code == 404:
        return "NOT_FOUND", "Recurso não encontrado."
    return "HTTP_EXCEPTION", "Erro HTTP."


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = get_request_id(request)

    log_method = logger.error if exc.status_code >= 500 else logger.warning
    log_method(
        "handled_app_exception request_id=%s status_code=%s code=%s path=%s method=%s",
        request_id,
        exc.status_code,
        exc.code,
        request.url.path,
        request.method,
    )

    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = get_request_id(request)
    code, message = _map_http_exception(exc)

    logger.warning(
        "handled_http_exception request_id=%s status_code=%s code=%s path=%s method=%s",
        request_id,
        exc.status_code,
        code,
        request.url.path,
        request.method,
    )

    details = None
    if exc.status_code not in {401, 403, 404} and exc.detail:
        details = exc.detail

    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = get_request_id(request)

    details = []
    for error in exc.errors():
        location_items = [str(item) for item in error.get("loc", ())]
        location = location_items[0] if location_items else "unknown"
        field = ".".join(location_items[1:]) if len(location_items) > 1 else None

        details.append(
            ValidationErrorDetail(
                location=location,
                field=field,
                message=error["msg"],
            ).model_dump()
        )

    logger.warning(
        "handled_validation_exception request_id=%s path=%s method=%s errors_count=%s",
        request_id,
        request.url.path,
        request.method,
        len(details),
    )

    return _build_error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Erro de validação na requisição.",
        details=details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)

    logger.exception(
        "unhandled_exception request_id=%s path=%s method=%s",
        request_id,
        request.url.path,
        request.method,
    )

    return _build_error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="Ocorreu um erro interno inesperado.",
        details=None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
