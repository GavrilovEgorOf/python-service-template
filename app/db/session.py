from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    pass


def init_engine(database_url: str | None = None) -> AsyncEngine:
    global engine, SessionLocal
    url = database_url or settings.database_url
    engine = create_async_engine(url, echo=settings.debug, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine


async def dispose_engine() -> None:
    global engine, SessionLocal
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        init_engine()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        yield session
