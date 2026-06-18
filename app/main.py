from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.middleware.audit import AuditMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware.request_id import RequestIdMiddleware
from app.api.routes.v1 import health
from app.api.v1_router import v1_router
from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.core.metrics import setup_metrics
from app.core.telemetry import setup_fastapi_telemetry


def create_app() -> FastAPI:
    setup_logging()
    docs_url = "/docs" if settings.debug else None
    redoc_url = "/redoc" if settings.debug else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=bool(settings.cors_origin_list),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)
    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    app.include_router(health.router, prefix="/health")

    setup_metrics(app)
    setup_fastapi_telemetry(app)
    return app


app = create_app()
