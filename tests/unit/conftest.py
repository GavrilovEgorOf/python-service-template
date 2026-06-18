import asyncio
from collections.abc import AsyncGenerator, Generator

import fakeredis.aioredis
import pytest
import pytest_asyncio
from app.core import redis as redis_module
from app.core.config import settings
from app.core.lifespan import lifespan
from app.db.session import Base, dispose_engine, get_db_session, init_engine
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

SQLITE_URL = "sqlite+aiosqlite:///:memory:"
TEST_API_KEY = "test-api-key"
TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests-32b-min"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "auth_disabled", True)
    monkeypatch.setattr(settings, "database_url", SQLITE_URL)
    monkeypatch.setattr(settings, "redis_url", None)
    monkeypatch.setattr(settings, "metrics_enabled", False)
    monkeypatch.setattr(settings, "otel_enabled", False)
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    monkeypatch.setattr(settings, "audit_log_persist", False)
    monkeypatch.setattr(settings, "api_key", TEST_API_KEY)
    monkeypatch.setattr(settings, "jwt_secret_key", TEST_JWT_SECRET)
    monkeypatch.setattr(settings, "debug", True)


@pytest_asyncio.fixture(autouse=True)
async def fake_redis(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[None, None]:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_module, "_redis", client)
    yield
    await client.aclose()
    monkeypatch.setattr(redis_module, "_redis", None)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    await dispose_engine()
    engine = create_async_engine(SQLITE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    init_engine(SQLITE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)

    async with lifespan(app), AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await dispose_engine()
    await engine.dispose()
