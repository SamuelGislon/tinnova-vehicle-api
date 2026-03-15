from decimal import Decimal, InvalidOperation

import redis
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.utils.money import quantize_exchange_rate

_redis_client: Redis | None = None


class ExchangeRateCacheError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class RedisCacheClient:
    USD_BRL_CACHE_KEY = "exchange_rate:usd_brl"

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def get_usd_brl_rate(self) -> Decimal | None:
        try:
            raw_value = self.redis_client.get(self.USD_BRL_CACHE_KEY)
        except RedisError as exc:
            raise ExchangeRateCacheError("cache_get_failed") from exc

        if raw_value is None:
            return None

        try:
            rate = quantize_exchange_rate(Decimal(str(raw_value)))
        except (InvalidOperation, TypeError, ValueError):
            return None

        if rate <= 0:
            return None

        return rate

    def set_usd_brl_rate(self, rate: Decimal, ttl_seconds: int) -> None:
        normalized_rate = quantize_exchange_rate(rate)

        try:
            self.redis_client.set(
                self.USD_BRL_CACHE_KEY,
                str(normalized_rate),
                ex=ttl_seconds,
            )
        except RedisError as exc:
            raise ExchangeRateCacheError("cache_set_failed") from exc


def get_redis_client() -> Redis:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


def ping_redis() -> bool:
    client = get_redis_client()
    return bool(client.ping())


def close_redis() -> None:
    global _redis_client

    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
