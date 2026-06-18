from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.domain.user import UserContext

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
) -> UserContext:
    if settings.auth_disabled:
        return UserContext(user_id="anonymous", roles=("user", "admin"))

    if api_key and settings.api_key and api_key == settings.api_key:
        return UserContext(user_id="api-key-client", roles=("user",))

    if credentials is not None and credentials.scheme.lower() == "bearer":
        # Stub: replace with JWT validation (issuer, audience, signature).
        token = credentials.credentials.strip()
        if token:
            return UserContext(user_id=f"bearer:{token[:8]}", roles=("user",))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(role: str) -> Callable[..., Awaitable[UserContext]]:
    async def _require_role(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(role) and not user.has_role("admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return _require_role
