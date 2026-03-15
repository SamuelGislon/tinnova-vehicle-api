from decimal import Decimal

import httpx
import pytest

from app.integrations.exchange_rate_client import (
    ExchangeRateClient,
    ExchangeRateProviderError,
)

pytestmark = pytest.mark.unit


def test_fetch_primary_usd_brl_rate_parses_awesomeapi_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://primary.test"
        return httpx.Response(
            200,
            json={
                "USDBRL": {
                    "code": "USD",
                    "codein": "BRL",
                    "bid": "5.7346",
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ExchangeRateClient(
            http_client=http_client,
            primary_url="https://primary.test",
            fallback_url="https://fallback.test",
        )

        assert client.fetch_primary_usd_brl_rate() == Decimal("5.7346")


def test_fetch_fallback_usd_brl_rate_parses_frankfurter_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://fallback.test"
        return httpx.Response(
            200,
            json={
                "base": "USD",
                "date": "2026-03-15",
                "rates": {
                    "BRL": 5.8123,
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ExchangeRateClient(
            http_client=http_client,
            primary_url="https://primary.test",
            fallback_url="https://fallback.test",
        )

        assert client.fetch_fallback_usd_brl_rate() == Decimal("5.8123")


def test_fetch_primary_invalid_payload_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ExchangeRateClient(
            http_client=http_client,
            primary_url="https://primary.test",
            fallback_url="https://fallback.test",
        )

        with pytest.raises(ExchangeRateProviderError) as exc:
            client.fetch_primary_usd_brl_rate()

    assert exc.value.provider == "awesomeapi"
    assert exc.value.reason == "invalid_payload"


def test_fetch_fallback_invalid_rate_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"rates": {"BRL": 0}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ExchangeRateClient(
            http_client=http_client,
            primary_url="https://primary.test",
            fallback_url="https://fallback.test",
        )

        with pytest.raises(ExchangeRateProviderError) as exc:
            client.fetch_fallback_usd_brl_rate()

    assert exc.value.provider == "frankfurter"
    assert exc.value.reason == "invalid_rate"
