import logging
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings
from app.utils.money import quantize_exchange_rate

logger = logging.getLogger(__name__)


class ExchangeRateProviderError(Exception):
    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"{provider}:{reason}")


class ExchangeRateClient:
    def __init__(
        self,
        *,
        http_client: httpx.Client,
        primary_url: str | None = None,
        fallback_url: str | None = None,
    ) -> None:
        self.http_client = http_client
        self.primary_url = primary_url or settings.exchange_rate_primary_url
        self.fallback_url = fallback_url or settings.exchange_rate_fallback_url

    def fetch_primary_usd_brl_rate(self) -> Decimal:
        payload = self._get_json(self.primary_url, provider="awesomeapi")
        return self._parse_primary_payload(payload)

    def fetch_fallback_usd_brl_rate(self) -> Decimal:
        payload = self._get_json(self.fallback_url, provider="frankfurter")
        return self._parse_fallback_payload(payload)

    def _get_json(self, url: str, *, provider: str) -> dict:
        try:
            response = self.http_client.get(
                url,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("exchange_rate_timeout provider=%s", provider)
            raise ExchangeRateProviderError(provider, "timeout") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "exchange_rate_http_error provider=%s status=%s",
                provider,
                exc.response.status_code,
            )
            raise ExchangeRateProviderError(
                provider,
                f"http_status_{exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("exchange_rate_request_error provider=%s", provider)
            raise ExchangeRateProviderError(provider, "request_error") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExchangeRateProviderError(provider, "invalid_json") from exc

        if not isinstance(payload, dict):
            raise ExchangeRateProviderError(provider, "invalid_payload")

        return payload

    def _parse_primary_payload(self, payload: dict) -> Decimal:
        usd_brl = payload.get("USDBRL")

        if not isinstance(usd_brl, dict):
            raise ExchangeRateProviderError("awesomeapi", "invalid_payload")

        return self._parse_rate_value(
            provider="awesomeapi",
            raw_value=usd_brl.get("bid"),
        )

    def _parse_fallback_payload(self, payload: dict) -> Decimal:
        rates = payload.get("rates")

        if not isinstance(rates, dict):
            raise ExchangeRateProviderError("frankfurter", "invalid_payload")

        return self._parse_rate_value(
            provider="frankfurter",
            raw_value=rates.get("BRL"),
        )

    def _parse_rate_value(self, *, provider: str, raw_value: object) -> Decimal:
        try:
            rate = Decimal(str(raw_value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ExchangeRateProviderError(provider, "invalid_payload") from exc

        normalized_rate = quantize_exchange_rate(rate)

        if normalized_rate <= 0:
            raise ExchangeRateProviderError(provider, "invalid_rate")

        return normalized_rate
