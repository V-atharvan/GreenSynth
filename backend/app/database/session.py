"""
GreenSynth Analytics — Async Database Session Factory

Provides:
  - async_engine       : The SQLAlchemy async engine (singleton)
  - AsyncSessionLocal  : Session factory for creating AsyncSession instances
  - get_db()           : FastAPI dependency that yields a database session
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Engine ─────────────────────────────────────────────────
# echo=False in production; set echo=True only for debugging SQL
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,   # Detect stale connections
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── FastAPI dependency ─────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession.

    Usage in route handlers:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...

    The session is committed on success and rolled back on exception.
    It is always closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
