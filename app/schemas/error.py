from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ValidationErrorDetail(BaseModel):
    location: str
    field: str | None = None
    message: str


class ErrorContent(BaseModel):
    code: str
    message: str
    details: Any = None
    path: str
    method: str
    timestamp: datetime
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorContent
