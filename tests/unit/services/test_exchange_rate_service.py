from decimal import Decimal

import pytest

from app.core.exceptions import ServiceUnavailableException
from app.integrations.exchange_rate_client import ExchangeRateProviderError
from app.integrations.redis_client import ExchangeRateCacheError
from app.services.exchange_rate_service import ExchangeRateService

pytestmark = pytest.mark.unit


class FakeExchangeRateClient:
    def __init__(
        self,
        *,
        primary_rate: Decimal | None = None,
        fallback_rate: Decimal | None = None,
        primary_error: ExchangeRateProviderError | None = None,
        fallback_error: ExchangeRateProviderError | None = None,
    ) -> None:
        self.primary_rate = primary_rate
        self.fallback_rate = fallback_rate
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        self.primary_calls = 0
        self.fallback_calls = 0

    def fetch_primary_usd_brl_rate(self) -> Decimal:
        self.primary_calls += 1
        if self.primary_error is not None:
            raise self.primary_error
        assert self.primary_rate is not None
        return self.primary_rate

    def fetch_fallback_usd_brl_rate(self) -> Decimal:
        self.fallback_calls += 1
        if self.fallback_error is not None:
            raise self.fallback_error
        assert self.fallback_rate is not None
        return self.fallback_rate


class FakeCacheClient:
    def __init__(
        self,
        *,
        cached_rate: Decimal | None = None,
        fail_on_get: bool = False,
        fail_on_set: bool = False,
    ) -> None:
        self.cached_rate = cached_rate
        self.fail_on_get = fail_on_get
        self.fail_on_set = fail_on_set
        self.last_ttl: int | None = None

    def get_usd_brl_rate(self) -> Decimal | None:
        if self.fail_on_get:
            raise ExchangeRateCacheError("cache_get_failed")
        return self.cached_rate

    def set_usd_brl_rate(self, rate: Decimal, ttl_seconds: int) -> None:
        if self.fail_on_set:
            raise ExchangeRateCacheError("cache_set_failed")
        self.cached_rate = rate
        self.last_ttl = ttl_seconds


def test_get_usd_brl_rate_reads_from_cache_first() -> None:
    cache = FakeCacheClient(cached_rate=Decimal("5.5000"))
    client = FakeExchangeRateClient(primary_rate=Decimal("5.7000"))
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    result = service.get_usd_brl_rate()

    assert result == Decimal("5.5000")
    assert client.primary_calls == 0
    assert client.fallback_calls == 0


def test_get_usd_brl_rate_uses_primary_when_cache_is_empty() -> None:
    cache = FakeCacheClient()
    client = FakeExchangeRateClient(primary_rate=Decimal("5.7346"))
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    result = service.get_usd_brl_rate()

    assert result == Decimal("5.7346")
    assert cache.cached_rate == Decimal("5.7346")
    assert cache.last_ttl == 300
    assert client.primary_calls == 1
    assert client.fallback_calls == 0


def test_get_usd_brl_rate_uses_fallback_when_primary_fails() -> None:
    cache = FakeCacheClient()
    client = FakeExchangeRateClient(
        primary_error=ExchangeRateProviderError("awesomeapi", "timeout"),
        fallback_rate=Decimal("5.8100"),
    )
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    result = service.get_usd_brl_rate()

    assert result == Decimal("5.8100")
    assert cache.cached_rate == Decimal("5.8100")
    assert client.primary_calls == 1
    assert client.fallback_calls == 1


def test_get_usd_brl_rate_raises_when_both_providers_fail() -> None:
    cache = FakeCacheClient()
    client = FakeExchangeRateClient(
        primary_error=ExchangeRateProviderError("awesomeapi", "timeout"),
        fallback_error=ExchangeRateProviderError("frankfurter", "http_status_503"),
    )
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    with pytest.raises(ServiceUnavailableException) as exc:
        service.get_usd_brl_rate()

    assert exc.value.code == "EXCHANGE_RATE_UNAVAILABLE"
    assert exc.value.status_code == 503


def test_get_usd_brl_rate_raises_when_provider_returns_invalid_rate() -> None:
    cache = FakeCacheClient()
    client = FakeExchangeRateClient(primary_rate=Decimal("0"))
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    with pytest.raises(ServiceUnavailableException) as exc:
        service.get_usd_brl_rate()

    assert exc.value.code == "INVALID_EXCHANGE_RATE"


def test_convert_brl_to_usd_uses_decimal_correctly() -> None:
    cache = FakeCacheClient(cached_rate=Decimal("5.0000"))
    client = FakeExchangeRateClient(primary_rate=Decimal("5.7000"))
    service = ExchangeRateService(
        exchange_rate_client=client,
        cache_client=cache,
        ttl_seconds=300,
    )

    result = service.convert_brl_to_usd(Decimal("100.00"))

    assert result == Decimal("20.00")
