from decimal import Decimal

import pytest

from app.api.dependencies.services import get_exchange_rate_service
from app.main import app
from app.repositories.vehicle_repository import VehicleRepository
from tests.assertions import assert_standard_error_payload
from tests.helpers import FailingExchangeRateService, create_vehicle

pytestmark = pytest.mark.integration


def make_vehicle_payload(
    *,
    brand: str = "Toyota",
    model: str = "Corolla",
    year: int = 2022,
    color: str = "Prata",
    plate: str = "ABC1D23",
    price_brl: str = "125000.00",
) -> dict:
    return {
        "brand": brand,
        "model": model,
        "year": year,
        "color": color,
        "plate": plate,
        "price_brl": price_brl,
    }


def test_user_can_access_vehicle_get_endpoints(client, user_auth_headers, db_session) -> None:
    vehicle = create_vehicle(db_session, plate="AAA1A11")

    list_response = client.get("/api/v1/veiculos", headers=user_auth_headers)
    detail_response = client.get(f"/api/v1/veiculos/{vehicle.id}", headers=user_auth_headers)

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == vehicle.id


@pytest.mark.parametrize(
    ("method", "path_template", "payload"),
    [
        ("POST", "/api/v1/veiculos", make_vehicle_payload(plate="AAA1A11")),
        ("PUT", "/api/v1/veiculos/{id}", make_vehicle_payload(plate="BBB1B11")),
        ("PATCH", "/api/v1/veiculos/{id}", {"color": "Preto"}),
        ("DELETE", "/api/v1/veiculos/{id}", None),
    ],
)
def test_user_receives_403_on_write_endpoints(
    client,
    user_auth_headers,
    db_session,
    method,
    path_template,
    payload,
) -> None:
    vehicle = create_vehicle(db_session, plate="USR1A11")
    path = path_template.format(id=vehicle.id)

    response = client.request(method, path, headers=user_auth_headers, json=payload)

    error = assert_standard_error_payload(
        response,
        expected_status=403,
        expected_code="FORBIDDEN",
    )
    assert error["message"] == "Acesso restrito a administradores."


def test_admin_can_create_vehicle(client, admin_auth_headers) -> None:
    response = client.post(
        "/api/v1/veiculos",
        headers=admin_auth_headers,
        json=make_vehicle_payload(plate="BRA2E19"),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["plate"] == "BRA2E19"
    assert Decimal(payload["price_usd"]) == Decimal("25000.00")
    assert payload["is_active"] is True


def test_admin_can_update_vehicle_with_put(client, admin_auth_headers, db_session) -> None:
    vehicle = create_vehicle(db_session, plate="AAA1A11")

    response = client.put(
        f"/api/v1/veiculos/{vehicle.id}",
        headers=admin_auth_headers,
        json=make_vehicle_payload(
            brand="Honda",
            model="Civic",
            year=2023,
            color="Preto",
            plate="BBB1B11",
            price_brl="150000.00",
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["brand"] == "Honda"
    assert payload["model"] == "Civic"
    assert payload["year"] == 2023
    assert payload["color"] == "Preto"
    assert payload["plate"] == "BBB1B11"
    assert Decimal(payload["price_usd"]) == Decimal("30000.00")


def test_admin_can_update_vehicle_with_patch(client, admin_auth_headers, db_session) -> None:
    vehicle = create_vehicle(db_session, plate="AAA1A11", price_usd=Decimal("25000.00"))

    response = client.patch(
        f"/api/v1/veiculos/{vehicle.id}",
        headers=admin_auth_headers,
        json={"color": "Preto", "price_brl": "130000.00"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["brand"] == "Toyota"
    assert payload["color"] == "Preto"
    assert Decimal(payload["price_usd"]) == Decimal("26000.00")


def test_admin_can_soft_delete_vehicle(
    client,
    admin_auth_headers,
    db_session,
    session_factory,
) -> None:
    vehicle = create_vehicle(db_session, plate="AAA1A11")

    delete_response = client.delete(
        f"/api/v1/veiculos/{vehicle.id}",
        headers=admin_auth_headers,
    )
    detail_response = client.get(
        f"/api/v1/veiculos/{vehicle.id}",
        headers=admin_auth_headers,
    )

    assert delete_response.status_code == 204

    error = assert_standard_error_payload(
        detail_response,
        expected_status=404,
        expected_code="VEHICLE_NOT_FOUND",
    )
    assert error["message"] == "Veículo não encontrado."

    with session_factory() as session:
        deleted = VehicleRepository(session).get_by_id(vehicle.id, include_inactive=True)
        assert deleted is not None
        assert deleted.is_active is False
        assert deleted.deleted_at is not None


def test_get_by_id_does_not_return_inactive_vehicle(client, user_auth_headers, db_session) -> None:
    vehicle = create_vehicle(db_session, plate="AAA1A11", is_active=False)

    response = client.get(f"/api/v1/veiculos/{vehicle.id}", headers=user_auth_headers)

    error = assert_standard_error_payload(
        response,
        expected_status=404,
        expected_code="VEHICLE_NOT_FOUND",
    )
    assert error["message"] == "Veículo não encontrado."


def test_list_vehicles_supports_filters_pagination_and_ordering(
    client,
    user_auth_headers,
    db_session,
) -> None:
    create_vehicle(db_session, brand="Toyota", plate="AAA1A11", price_usd=Decimal("30000.00"))
    create_vehicle(db_session, brand="Toyota", plate="AAA1A12", price_usd=Decimal("20000.00"))
    create_vehicle(db_session, brand="Honda", plate="BBB1B11", price_usd=Decimal("10000.00"))

    response = client.get(
        "/api/v1/veiculos"
        "?brand=Toyota"
        "&page=1"
        "&page_size=1"
        "&sort_by=price_usd"
        "&sort_order=asc",
        headers=user_auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["plate"] == "AAA1A12"


def test_create_vehicle_returns_409_when_plate_already_exists(
    client,
    admin_auth_headers,
    db_session,
) -> None:
    create_vehicle(db_session, plate="ABC1D23")

    response = client.post(
        "/api/v1/veiculos",
        headers=admin_auth_headers,
        json=make_vehicle_payload(plate="abc-1d23"),
    )

    error = assert_standard_error_payload(
        response,
        expected_status=409,
        expected_code="VEHICLE_ALREADY_EXISTS",
    )
    assert error["message"] == "Já existe um veículo cadastrado com esta placa."


def test_create_vehicle_returns_422_for_invalid_payload(client, admin_auth_headers) -> None:
    response = client.post(
        "/api/v1/veiculos",
        headers=admin_auth_headers,
        json={
            "brand": "",
            "model": "Corolla",
            "year": 1800,
            "color": "Prata",
            "plate": "placa-invalida",
            "price_brl": "0",
        },
    )

    error = assert_standard_error_payload(
        response,
        expected_status=422,
        expected_code="VALIDATION_ERROR",
    )
    assert isinstance(error["details"], list)
    assert len(error["details"]) > 0


def test_create_vehicle_returns_503_when_exchange_rate_is_unavailable(
    client,
    admin_auth_headers,
) -> None:
    app.dependency_overrides[get_exchange_rate_service] = lambda: FailingExchangeRateService()

    response = client.post(
        "/api/v1/veiculos",
        headers=admin_auth_headers,
        json=make_vehicle_payload(plate="ZZZ9Z99"),
    )

    error = assert_standard_error_payload(
        response,
        expected_status=503,
        expected_code="EXCHANGE_RATE_UNAVAILABLE",
    )
    assert error["message"] == "Não foi possível obter a cotação USD/BRL nos provedores externos."
