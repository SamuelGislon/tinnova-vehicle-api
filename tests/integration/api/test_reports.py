import pytest

from tests.helpers import create_vehicle

pytestmark = pytest.mark.integration


def test_report_by_brand_counts_only_active_vehicles(client, user_auth_headers, db_session) -> None:
    create_vehicle(db_session, brand="Toyota", plate="AAA1A11")
    create_vehicle(db_session, brand="Toyota", plate="AAA1A12")
    create_vehicle(db_session, brand="Honda", plate="BBB1B11")
    create_vehicle(db_session, brand="Ford", plate="CCC1C11", is_active=False)

    response = client.get("/api/v1/veiculos/relatorios/por-marca", headers=user_auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_brands"] == 2
    assert payload["total_active_vehicles"] == 3
    assert payload["items"] == [
        {"brand": "Toyota", "total_active_vehicles": 2},
        {"brand": "Honda", "total_active_vehicles": 1},
    ]
    assert payload["generated_at"] is not None


def test_report_returns_empty_structure_for_empty_database(client, user_auth_headers) -> None:
    response = client.get("/api/v1/veiculos/relatorios/por-marca", headers=user_auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total_brands"] == 0
    assert payload["total_active_vehicles"] == 0
    assert payload["generated_at"] is not None
