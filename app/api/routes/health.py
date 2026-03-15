from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal
from app.integrations.redis_client import ping_redis
from app.schemas.common import HealthLiveResponse, HealthReadyResponse

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=HealthLiveResponse)
def liveness() -> HealthLiveResponse:
    return HealthLiveResponse(status="ok")


@router.get("/health/ready", response_model=HealthReadyResponse)
def readiness() -> HealthReadyResponse:
    database_status = "ok"
    redis_status = "ok"

    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    try:
        ping_redis()
    except Exception:
        redis_status = "error"

    overall_status = "ok" if database_status == "ok" and redis_status == "ok" else "degraded"

    return HealthReadyResponse(
        status=overall_status,
        database=database_status,
        redis=redis_status,
    )
