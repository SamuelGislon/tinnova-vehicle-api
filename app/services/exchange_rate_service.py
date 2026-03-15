import logging
from decimal import Decimal
from typing import Protocol

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.integrations.exchange_rate_client import (
    ExchangeRateClient,
    ExchangeRateProviderError,
)
from app.integrations.redis_client import ExchangeRateCacheError
from app.utils.money import quantize_exchange_rate, quantize_money

logger = logging.getLogger(__name__)


class ExchangeRateServiceProtocol(Protocol):
    def get_usd_brl_rate(self) -> Decimal: ...

    def convert_brl_to_usd(self, amount_brl: Decimal) -> Decimal: ...


class ExchangeRateCacheProtocol(Protocol):
    def get_usd_brl_rate(self) -> Decimal | None: ...

    def set_usd_brl_rate(self, rate: Decimal, ttl_seconds: int) -> None: ...


class ExchangeRateService:
    def __init__(
        self,
        *,
        exchange_rate_client: ExchangeRateClient,
        cache_client: ExchangeRateCacheProtocol,
        ttl_seconds: int | None = None,
    ) -> None:
        self.exchange_rate_client = exchange_rate_client
        self.cache_client = cache_client
        self.ttl_seconds = ttl_seconds or settings.redis_ttl_usd_brl

    def get_usd_brl_rate(self) -> Decimal:
        cached_rate = self._read_cache()

        if cached_rate is not None:
            logger.info("exchange_rate_cache_hit key=exchange_rate:usd_brl")
            return self._ensure_valid_rate(cached_rate, source="cache")

        logger.info("exchange_rate_cache_miss key=exchange_rate:usd_brl")

        try:
            rate = self.exchange_rate_client.fetch_primary_usd_brl_rate()
            logger.info("exchange_rate_provider_success provider=awesomeapi")
        except ExchangeRateProviderError as primary_error:
            logger.warning(
                "exchange_rate_provider_failed provider=%s reason=%s",
                primary_error.provider,
                primary_error.reason,
            )
            try:
                rate = self.exchange_rate_client.fetch_fallback_usd_brl_rate()
                logger.info("exchange_rate_provider_success provider=frankfurter")
            except ExchangeRateProviderError as fallback_error:
                logger.error(
                    "exchange_rate_providers_unavailable primary_reason=%s fallback_reason=%s",
                    primary_error.reason,
                    fallback_error.reason,
                )
                raise ServiceUnavailableException(
                    message="Não foi possível obter a cotação USD/BRL nos provedores externos.",
                    code="EXCHANGE_RATE_UNAVAILABLE",
                    details={
                        "primary": primary_error.reason,
                        "fallback": fallback_error.reason,
                    },
                ) from fallback_error

        valid_rate = self._ensure_valid_rate(rate, source="provider")
        self._write_cache(valid_rate)
        return valid_rate

    def convert_brl_to_usd(self, amount_brl: Decimal) -> Decimal:
        rate = self.get_usd_brl_rate()
        return quantize_money(amount_brl / rate)

    def _read_cache(self) -> Decimal | None:
        try:
            return self.cache_client.get_usd_brl_rate()
        except ExchangeRateCacheError as exc:
            logger.warning("exchange_rate_cache_failed operation=get reason=%s", exc.reason)
            return None

    def _write_cache(self, rate: Decimal) -> None:
        try:
            self.cache_client.set_usd_brl_rate(rate, self.ttl_seconds)
        except ExchangeRateCacheError as exc:
            logger.warning("exchange_rate_cache_failed operation=set reason=%s", exc.reason)

    def _ensure_valid_rate(self, rate: Decimal, *, source: str) -> Decimal:
        normalized_rate = quantize_exchange_rate(rate)

        if normalized_rate <= 0:
            raise ServiceUnavailableException(
                message="Cotação USD/BRL inválida recebida do serviço externo.",
                code="INVALID_EXCHANGE_RATE",
                details={"source": source},
            )

        return normalized_rate
