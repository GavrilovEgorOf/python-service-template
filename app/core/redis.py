from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None  # type: ignore[type-arg]


async def init_redis() -> Redis | None:  # type: ignore[type-arg]
    global _redis
    if not settings.redis_url:
        return None
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    await client.ping()
    _redis = client
    return client


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close(close_connection_pool=True)  # type: ignore[attr-defined]
        _redis = None


def get_redis() -> Redis | None:  # type: ignore[type-arg]
    return _redis


async def ping_redis() -> bool:
    client = get_redis()
    if client is None:
        return False
    await client.ping()
    return True


async def cache_get(key: str) -> str | None:
    client = get_redis()
    if client is None:
        return None
    value = await client.get(key)
    return value if isinstance(value, str) else None


async def cache_set(key: str, value: str, ttl_seconds: int | None = None) -> None:
    client = get_redis()
    if client is None:
        return
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
    await client.setex(key, ttl, value)


async def cache_delete(key: str) -> None:
    client = get_redis()
    if client is None:
        return
    await client.delete(key)


async def idempotency_get(key: str) -> dict[str, Any] | None:
    import json

    raw = await cache_get(f"idempotency:{key}")
    if raw is None:
        return None
    parsed: dict[str, Any] = json.loads(raw)
    return parsed


async def idempotency_store(key: str, payload: dict[str, Any]) -> None:
    import json

    await cache_set(
        f"idempotency:{key}",
        json.dumps(payload),
        ttl_seconds=settings.idempotency_ttl_seconds,
    )
