import hashlib
import json
from typing import Any

from app.core.redis import idempotency_get, idempotency_store
from app.domain.exceptions import IdempotencyConflictError


def request_fingerprint(body: dict[str, Any]) -> str:
    serialized = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


async def begin_idempotent_request(
    key: str,
    body: dict[str, Any],
) -> dict[str, Any] | None:
    existing = await idempotency_get(key)
    if existing is None:
        return None
    if existing.get("request_hash") != request_fingerprint(body):
        raise IdempotencyConflictError
    return existing


async def complete_idempotent_request(
    key: str,
    body: dict[str, Any],
    *,
    status_code: int,
    response_body: dict[str, Any],
) -> None:
    await idempotency_store(
        key,
        {
            "request_hash": request_fingerprint(body),
            "status_code": status_code,
            "response_body": response_body,
        },
    )
