"""Database configuration and session management.

Uses SQLAlchemy 2.x async with aiosqlite for SQLite.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ...core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


settings = get_settings()

# Ensure database directory exists
db_path = settings.database_path
db_path.parent.mkdir(parents=True, exist_ok=True)

async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables (create all if not exist)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
