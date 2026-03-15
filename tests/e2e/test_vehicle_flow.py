from decimal import Decimal

import pytest

from tests.assertions import assert_standard_error_payload
from tests.helpers import TEST_ADMIN_CREDENTIALS, get_access_token

pytestmark = pytest.mark.e2e


def test_admin_vehicle_flow_end_to_end(client) -> None:
    access_token = get_access_token(
        client,
        username=TEST_ADMIN_CREDENTIALS["username"],
        password=TEST_ADMIN_CREDENTIALS["password"],
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    create_response = client.post(
        "/api/v1/veiculos",
        headers=auth_headers,
        json={
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "color": "Prata",
            "plate": "ABC-1D23",
            "price_brl": "125000.00",
        },
    )
    assert create_response.status_code == 201
    created_vehicle = create_response.json()
    vehicle_id = created_vehicle["id"]
    assert created_vehicle["plate"] == "ABC1D23"
    assert Decimal(created_vehicle["price_usd"]) == Decimal("25000.00")

    list_response = client.get(
        "/api/v1/veiculos?brand=Toyota&plate=ABC1D23",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["id"] == vehicle_id

    detail_response = client.get(f"/api/v1/veiculos/{vehicle_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == vehicle_id

    patch_response = client.patch(
        f"/api/v1/veiculos/{vehicle_id}",
        headers=auth_headers,
        json={"color": "Preto", "price_brl": "130000.00"},
    )
    assert patch_response.status_code == 200
    patched_vehicle = patch_response.json()
    assert patched_vehicle["color"] == "Preto"
    assert Decimal(patched_vehicle["price_usd"]) == Decimal("26000.00")

    report_response = client.get("/api/v1/veiculos/relatorios/por-marca", headers=auth_headers)
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["total_active_vehicles"] == 1
    assert report_payload["items"] == [
        {"brand": "Toyota", "total_active_vehicles": 1},
    ]

    delete_response = client.delete(f"/api/v1/veiculos/{vehicle_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    detail_after_delete = client.get(f"/api/v1/veiculos/{vehicle_id}", headers=auth_headers)
    error = assert_standard_error_payload(
        detail_after_delete,
        expected_status=404,
        expected_code="VEHICLE_NOT_FOUND",
    )
    assert error["message"] == "Veículo não encontrado."

    list_after_delete = client.get(
        "/api/v1/veiculos?plate=ABC1D23",
        headers=auth_headers,
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["total"] == 0
    assert list_after_delete.json()["items"] == []
