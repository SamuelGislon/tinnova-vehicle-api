from typing import cast
from uuid import uuid4

from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return str(request_id)
    return "unknown"


def register_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id

        response = cast(Response, await call_next(request))
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
