from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_access_token
from app.domain.exceptions import AuthenticationError
from app.domain.user import UserContext

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
metrics_api_key_header = APIKeyHeader(name="X-Metrics-Key", auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
) -> UserContext:
    if settings.auth_disabled:
        user = UserContext(user_id="anonymous", roles=("user",))
        request.state.user_id = user.user_id
        return user

    if api_key and settings.api_key and api_key == settings.api_key:
        user = UserContext(user_id="api-key-client", roles=("user",))
        request.state.user_id = user.user_id
        return user

    if credentials is not None and credentials.scheme.lower() == "bearer":
        try:
            payload = decode_access_token(credentials.credentials.strip())
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )
        raw_roles = payload.get("roles", ["user"])
        roles = tuple(raw_roles) if isinstance(raw_roles, list) else ("user",)
        user = UserContext(user_id=subject, roles=roles)
        request.state.user_id = user.user_id
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_metrics_access(
    metrics_key: str | None = Security(metrics_api_key_header),
    api_key: str | None = Security(api_key_header),
) -> None:
    if not settings.metrics_enabled:
        return
    expected = settings.effective_metrics_api_key
    if expected is None:
        if settings.is_production:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Metrics disabled")
        return
    provided = metrics_key or api_key
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid metrics credentials"
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
