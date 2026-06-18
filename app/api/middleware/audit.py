import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.audit_log_enabled:
            return await call_next(request)

        response = await call_next(request)
        user_id = getattr(request.state, "user_id", "anonymous")
        logger.info(
            "audit_event",
            user_id=user_id,
            request_id=getattr(request.state, "request_id", None),
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        if settings.audit_log_persist:
            from app.services.audit_service import persist_audit_event

            await persist_audit_event(
                user_id=str(user_id),
                request_id=getattr(request.state, "request_id", None),
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )
        return response
