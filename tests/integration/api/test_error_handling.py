from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_authenticated_user
from app.api.dependencies.services import get_report_service
from app.main import app
from tests.assertions import assert_standard_error_payload

pytestmark = pytest.mark.integration


class BrokenReportService:
    def get_vehicles_by_brand_report(self):
        raise RuntimeError("unexpected boom")


def fake_user():
    return SimpleNamespace(
        id=1,
        username="user",
        email="user@test.local",
        role="USER",
        is_active=True,
    )


def test_returns_401_without_token(client) -> None:
    response = client.get("/api/v1/veiculos/relatorios/por-marca")

    error = assert_standard_error_payload(
        response,
        expected_status=401,
        expected_code="UNAUTHORIZED",
    )
    assert error["message"] == "Não autenticado."


def test_returns_401_with_invalid_token(client) -> None:
    response = client.get(
        "/api/v1/veiculos/relatorios/por-marca",
        headers={"Authorization": "Bearer invalid-token"},
    )

    error = assert_standard_error_payload(
        response,
        expected_status=401,
        expected_code="UNAUTHORIZED",
    )
    assert error["message"] == "Token inválido ou expirado."


def test_returns_500_for_unexpected_exception() -> None:
    app.dependency_overrides[require_authenticated_user] = fake_user
    app.dependency_overrides[get_report_service] = lambda: BrokenReportService()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/veiculos/relatorios/por-marca")

    error = assert_standard_error_payload(
        response,
        expected_status=500,
        expected_code="INTERNAL_SERVER_ERROR",
    )
    assert error["message"] == "Ocorreu um erro interno inesperado."
    assert error["details"] is None

    app.dependency_overrides.clear()


def test_error_payload_preserves_request_id_header(client) -> None:
    request_id = "test-request-id-123"

    response = client.get(
        "/api/v1/veiculos/relatorios/por-marca",
        headers={"X-Request-ID": request_id},
    )

    error = assert_standard_error_payload(
        response,
        expected_status=401,
        expected_code="UNAUTHORIZED",
    )
    assert response.headers["x-request-id"] == request_id
    assert error["request_id"] == request_id
