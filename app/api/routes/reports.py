from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_authenticated_user
from app.api.dependencies.services import get_report_service
from app.db.models.user import User
from app.schemas.report import BrandReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/veiculos/relatorios", tags=["Reports"])


@router.get(
    "/por-marca",
    response_model=BrandReportResponse,
    summary="Gerar relatório de veículos ativos por marca",
)
def get_vehicles_by_brand_report(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
) -> BrandReportResponse:
    _ = current_user
    return report_service.get_vehicles_by_brand_report()
