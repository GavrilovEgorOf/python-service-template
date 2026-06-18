import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import rate_limit_check

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        if not request.url.path.startswith(f"{settings.api_v1_prefix}/items"):
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        identifier = api_key or client_host

        allowed, remaining = await rate_limit_check(identifier)
        if not allowed:
            logger.warning("rate_limit_exceeded", identifier=identifier, path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(settings.rate_limit_window_seconds)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
