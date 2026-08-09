"""
GreenSynth Analytics — FastAPI Dependencies

Provides dependency-injected objects for route handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.

    The session is committed on success, rolled back on any exception,
    and always closed after the request.
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
