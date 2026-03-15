from datetime import datetime

from pydantic import BaseModel


class BrandReportItem(BaseModel):
    brand: str
    total_active_vehicles: int


class BrandReportResponse(BaseModel):
    items: list[BrandReportItem]
    total_brands: int
    total_active_vehicles: int
    generated_at: datetime
