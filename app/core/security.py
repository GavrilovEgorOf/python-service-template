from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import DEFAULT_DEV_JWT_SECRET, settings
from app.domain.exceptions import AuthenticationError


def _jwt_secret() -> str:
    secret = settings.jwt_secret_key
    if not secret:
        if settings.is_production:
            raise AuthenticationError("JWT is not configured")
        return DEFAULT_DEV_JWT_SECRET
    return secret


def create_access_token(
    subject: str,
    *,
    roles: tuple[str, ...] = ("user",),
    expires_minutes: int = 60,
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "roles": list(roles),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc
    return payload
