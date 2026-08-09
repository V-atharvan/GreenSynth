"""
GreenSynth Analytics — Backend Test Configuration

Shared pytest fixtures for unit and integration tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database.base import Base
from app.main import app
from app.api.deps import get_db

# ── In-memory SQLite for tests ─────────────────────────────
# SQLite is used for testing speed and isolation.
# PostgreSQL-specific features (JSONB, UUID) should be checked
# in integration tests against a real PostgreSQL instance.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test SQLite engine with all tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a test database session that rolls back after each test.

    This ensures tests are isolated — no state bleeds between tests.
    """
    session_factory = async_sessionmaker(
        bind=test_engine, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP test client with the test DB injected.

    Overrides the get_db dependency so tests use the test session.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Sample fixtures ────────────────────────────────────────

@pytest_asyncio.fixture
async def demo_project(db_session: AsyncSession):
    """Create a demo project for tests."""
    from app.models.project import Project

    project = Project(
        project_code="TEST-P7",
        name="Test Project 7",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status="ACTIVE",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def demo_experiment(db_session: AsyncSession, demo_project):
    """Create a demo experiment for tests."""
    from app.models.experiment import Experiment

    experiment = Experiment(
        project_id=demo_project.id,
        experiment_code="TEST-EXP-001",
        title="Test Experiment 001",
        status="PLANNED",
        researcher="Test Researcher",
    )
    db_session.add(experiment)
    await db_session.flush()
    await db_session.refresh(experiment)
    return experiment


@pytest_asyncio.fixture
async def demo_sample(db_session: AsyncSession, demo_experiment):
    """Create a demo sample for tests."""
    from app.models.sample import Sample

    sample = Sample(
        experiment_id=demo_experiment.id,
        sample_code="TEST-S001",
        name="Test Sample 001",
        material="CuO",
        status="PREPARED",
    )
    db_session.add(sample)
    await db_session.flush()
    await db_session.refresh(sample)
    return sample
