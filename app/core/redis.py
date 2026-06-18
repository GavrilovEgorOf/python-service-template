import json
from enum import Enum
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None  # type: ignore[type-arg]


class IdempotencyStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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
        await _redis.close(close_connection_pool=True)
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


async def cache_delete_pattern(pattern: str) -> None:
    client = get_redis()
    if client is None:
        return
    async for key in client.scan_iter(match=pattern):
        await client.delete(key)


def _idempotency_redis_key(key: str) -> str:
    return f"idempotency:{key}"


async def idempotency_acquire(
    key: str,
    request_hash: str,
) -> tuple[str, dict[str, Any] | None]:
    """Return (state, payload) where state is acquired|completed|conflict|in_progress."""
    client = get_redis()
    if client is None:
        return "acquired", None

    redis_key = _idempotency_redis_key(key)
    lock_payload = json.dumps(
        {"status": IdempotencyStatus.IN_PROGRESS, "request_hash": request_hash},
    )
    acquired = await client.set(
        redis_key,
        lock_payload,
        nx=True,
        ex=settings.idempotency_lock_ttl_seconds,
    )
    if acquired:
        return "acquired", None

    raw = await client.get(redis_key)
    if raw is None:
        return "acquired", None

    payload: dict[str, Any] = json.loads(raw)
    existing_hash = payload.get("request_hash")
    if existing_hash != request_hash:
        return "conflict", None

    status = payload.get("status")
    if status == IdempotencyStatus.COMPLETED:
        return "completed", payload
    return "in_progress", None


async def idempotency_complete(
    key: str,
    request_hash: str,
    *,
    status_code: int,
    response_body: dict[str, Any],
) -> None:
    client = get_redis()
    if client is None:
        return
    payload = json.dumps(
        {
            "status": IdempotencyStatus.COMPLETED,
            "request_hash": request_hash,
            "status_code": status_code,
            "response_body": response_body,
        }
    )
    await client.set(_idempotency_redis_key(key), payload, ex=settings.idempotency_ttl_seconds)


async def idempotency_release(key: str) -> None:
    client = get_redis()
    if client is None:
        return
    payload = await client.get(_idempotency_redis_key(key))
    if not payload:
        return
    parsed: dict[str, Any] = json.loads(payload)
    if parsed.get("status") == IdempotencyStatus.IN_PROGRESS:
        await client.delete(_idempotency_redis_key(key))


async def rate_limit_check(identifier: str) -> tuple[bool, int]:
    client = get_redis()
    if client is None or not settings.rate_limit_enabled:
        return True, 0

    window = settings.rate_limit_window_seconds
    bucket_key = f"ratelimit:{identifier}:{window}"
    count = await client.incr(bucket_key)
    if count == 1:
        await client.expire(bucket_key, window)
    remaining = max(settings.rate_limit_requests - int(count), 0)
    allowed = int(count) <= settings.rate_limit_requests
    return allowed, remaining
