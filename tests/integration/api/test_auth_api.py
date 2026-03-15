import pytest

from tests.assertions import assert_standard_error_payload

pytestmark = pytest.mark.integration


def test_login_with_success(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Admin123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] > 0


def test_login_with_invalid_credentials_returns_401(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "WrongPassword"},
    )

    error = assert_standard_error_payload(
        response,
        expected_status=401,
        expected_code="UNAUTHORIZED",
    )
    assert error["message"] == "Usuário ou senha inválidos."


def test_auth_me_returns_authenticated_user(client, admin_auth_headers) -> None:
    response = client.get("/api/v1/auth/me", headers=admin_auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin"
    assert payload["email"] == "admin@test.local"
    assert payload["role"] == "ADMIN"
    assert payload["is_active"] is True
