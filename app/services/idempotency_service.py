import hashlib
import json
from typing import Any

from app.core.redis import idempotency_acquire, idempotency_complete, idempotency_release
from app.domain.exceptions import (
    IdempotencyConflictError,
    IdempotencyInProgressError,
)


def request_fingerprint(body: dict[str, Any]) -> str:
    serialized = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


async def begin_idempotent_request(
    key: str,
    body: dict[str, Any],
) -> dict[str, Any] | None:
    fingerprint = request_fingerprint(body)
    state, payload = await idempotency_acquire(key, fingerprint)
    if state == "conflict":
        raise IdempotencyConflictError("Idempotency key reused with different payload")
    if state == "in_progress":
        raise IdempotencyInProgressError("Request with this idempotency key is already in progress")
    if state == "completed" and payload is not None:
        return payload
    return None


async def complete_idempotent_request(
    key: str,
    body: dict[str, Any],
    *,
    status_code: int,
    response_body: dict[str, Any],
) -> None:
    await idempotency_complete(
        key,
        request_fingerprint(body),
        status_code=status_code,
        response_body=response_body,
    )


async def fail_idempotent_request(key: str) -> None:
    await idempotency_release(key)
