from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.report import BrandReportItem, BrandReportResponse
from app.utils.datetime import utc_now


class ReportService:
    def __init__(self, vehicle_repository: VehicleRepository) -> None:
        self.vehicle_repository = vehicle_repository

    def get_vehicles_by_brand_report(self) -> BrandReportResponse:
        rows = self.vehicle_repository.get_brand_report_rows()

        items = [
            BrandReportItem(
                brand=brand,
                total_active_vehicles=total,
            )
            for brand, total in rows
        ]

        total_active_vehicles = sum(item.total_active_vehicles for item in items)

        return BrandReportResponse(
            items=items,
            total_brands=len(items),
            total_active_vehicles=total_active_vehicles,
            generated_at=utc_now(),
        )
