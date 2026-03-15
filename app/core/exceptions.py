from typing import Any


class AppException(Exception):
    def __init__(
        self,
        *,
        message: str,
        code: str,
        status_code: int,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.headers = headers or {}
        super().__init__(message)


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Requisição inválida.",
        code: str = "BAD_REQUEST",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Não autenticado.",
        code: str = "UNAUTHORIZED",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=401,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Acesso negado.",
        code: str = "FORBIDDEN",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=403,
            details=details,
        )


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Recurso não encontrado.",
        code: str = "NOT_FOUND",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            details=details,
        )


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Conflito de dados.",
        code: str = "CONFLICT",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details,
        )


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "Serviço indisponível.",
        code: str = "SERVICE_UNAVAILABLE",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=503,
            details=details,
        )
