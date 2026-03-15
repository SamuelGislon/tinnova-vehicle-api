from collections.abc import Generator
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.integrations.exchange_rate_client import ExchangeRateClient
from app.integrations.redis_client import RedisCacheClient, get_redis_client
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exchange_rate_service import ExchangeRateService, ExchangeRateServiceProtocol
from app.services.report_service import ReportService
from app.services.vehicle_service import VehicleService


def get_exchange_rate_client() -> Generator[ExchangeRateClient, None, None]:
    timeout = httpx.Timeout(settings.exchange_rate_timeout_seconds)

    with httpx.Client(timeout=timeout, trust_env=False) as http_client:
        yield ExchangeRateClient(http_client=http_client)


def get_exchange_rate_cache() -> RedisCacheClient:
    return RedisCacheClient(get_redis_client())


def get_exchange_rate_service(
    exchange_rate_client: Annotated[ExchangeRateClient, Depends(get_exchange_rate_client)],
    cache_client: Annotated[RedisCacheClient, Depends(get_exchange_rate_cache)],
) -> ExchangeRateServiceProtocol:
    return ExchangeRateService(
        exchange_rate_client=exchange_rate_client,
        cache_client=cache_client,
        ttl_seconds=settings.redis_ttl_usd_brl,
    )


def get_vehicle_service(
    db: Annotated[Session, Depends(get_db)],
    exchange_rate_service: Annotated[
        ExchangeRateServiceProtocol, Depends(get_exchange_rate_service)
    ],
) -> VehicleService:
    return VehicleService(
        vehicle_repository=VehicleRepository(db),
        exchange_rate_service=exchange_rate_service,
    )


def get_report_service(
    db: Annotated[Session, Depends(get_db)],
) -> ReportService:
    return ReportService(vehicle_repository=VehicleRepository(db))
