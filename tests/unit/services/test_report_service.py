import pytest

from app.services.report_service import ReportService

pytestmark = pytest.mark.unit


class FakeVehicleRepository:
    def __init__(self, rows: list[tuple[str, int]]) -> None:
        self.rows = rows

    def get_brand_report_rows(self) -> list[tuple[str, int]]:
        return self.rows


def test_report_service_builds_expected_response() -> None:
    service = ReportService(
        vehicle_repository=FakeVehicleRepository(
            rows=[
                ("Toyota", 2),
                ("Honda", 1),
            ]
        )
    )

    response = service.get_vehicles_by_brand_report()

    assert response.total_brands == 2
    assert response.total_active_vehicles == 3
    assert len(response.items) == 2
    assert response.items[0].brand == "Toyota"
    assert response.items[0].total_active_vehicles == 2
    assert response.items[1].brand == "Honda"
    assert response.items[1].total_active_vehicles == 1


def test_report_service_handles_empty_base() -> None:
    service = ReportService(vehicle_repository=FakeVehicleRepository(rows=[]))

    response = service.get_vehicles_by_brand_report()

    assert response.items == []
    assert response.total_brands == 0
    assert response.total_active_vehicles == 0
    assert response.generated_at is not None
