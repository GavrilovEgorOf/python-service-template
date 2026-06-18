import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from app.core import redis as redis_module
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import Base, dispose_engine, get_db_session, init_engine
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer


def _postgres_async_url() -> str:
    with PostgresContainer("postgres:16-alpine") as postgres:
        url = postgres.get_connection_url()
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def integration_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return _postgres_async_url()


@pytest.fixture(scope="session")
def integration_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(autouse=True)
def integration_settings(monkeypatch: pytest.MonkeyPatch, integration_database_url: str) -> None:
    monkeypatch.setattr(settings, "auth_disabled", True)
    monkeypatch.setattr(settings, "database_url", integration_database_url)
    monkeypatch.setattr(settings, "metrics_enabled", False)
    monkeypatch.setattr(settings, "otel_enabled", False)


@pytest_asyncio.fixture
async def integration_client(
    integration_database_url: str,
    integration_redis_url: str,
) -> AsyncGenerator[AsyncClient, None]:
    await dispose_engine()
    engine = init_engine(integration_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    redis_client = Redis.from_url(integration_redis_url, decode_responses=True)
    await redis_client.ping()
    redis_module._redis = redis_client
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(settings, "redis_url", integration_redis_url)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)

    async with lifespan(app), AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    monkeypatch.undo()
    app.dependency_overrides.clear()
    await redis_client.aclose()
    redis_module._redis = None
    await dispose_engine()
