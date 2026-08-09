"""
Alembic environment configuration for GreenSynth Analytics.

Uses an async engine for migrations (via asyncpg) so that only one
PostgreSQL driver is needed across the whole application.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ── Load Alembic logging config ────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import Base metadata ───────────────────────────────────
# This import must come AFTER fileConfig to avoid circular imports.
# Importing base.py also imports all models via its __init__ block,
# so Alembic's autogenerate can see all table definitions.
from app.database.base import Base  # noqa: E402

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get the database URL for migrations.

    Priority:
    1. DATABASE_URL_SYNC env var (psycopg2 sync driver)
    2. DATABASE_URL env var (asyncpg — used as-is for async migration)
    3. Alembic ini sqlalchemy.url (fallback)
    """
    # Try sync URL first (preferred for Alembic)
    sync_url = os.environ.get("DATABASE_URL_SYNC")
    if sync_url:
        return sync_url

    # Fall back to async URL
    async_url = os.environ.get("DATABASE_URL")
    if async_url:
        return async_url

    # Fall back to alembic.ini
    url = config.get_main_option("sqlalchemy.url", "")
    if not url:
        raise ValueError(
            "No database URL found. Set DATABASE_URL_SYNC or DATABASE_URL "
            "environment variable."
        )
    return url


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.

    Generates SQL statements for review before applying.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (asyncpg driver)."""
    url = get_database_url()

    # If we have a sync URL (psycopg2), use synchronous migration path
    if "psycopg2" in url:
        from sqlalchemy import create_engine

        connectable = create_engine(url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            do_run_migrations(connection)
        return

    # Async path (asyncpg)
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
