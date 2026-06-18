from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.redis import close_redis, init_redis, ping_redis
from app.core.startup import validate_runtime_settings
from app.core.telemetry import instrument_sqlalchemy
from app.db.session import dispose_engine, init_engine

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    validate_runtime_settings()
    init_engine(settings.database_url)
    redis = await init_redis()
    instrument_sqlalchemy()
    logger.info(
        "service_starting",
        app=settings.app_name,
        environment=settings.environment,
        redis_enabled=redis is not None,
    )
    try:
        yield
    finally:
        logger.info("service_stopping", app=settings.app_name)
        await close_redis()
        await dispose_engine()


async def verify_database() -> bool:
    from app.db.session import SessionLocal

    if SessionLocal is None:
        return False
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return True


async def verify_dependencies() -> dict[str, str]:
    status_map: dict[str, str] = {"database": "unavailable", "redis": "disabled"}
    try:
        if await verify_database():
            status_map["database"] = "ok"
    except Exception:
        status_map["database"] = "unavailable"

    if settings.redis_url:
        try:
            if await ping_redis():
                status_map["redis"] = "ok"
            else:
                status_map["redis"] = "unavailable"
        except Exception:
            status_map["redis"] = "unavailable"
    return status_map
