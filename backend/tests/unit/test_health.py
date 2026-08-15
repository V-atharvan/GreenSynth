"""
GreenSynth Analytics — Unit Tests: Health Endpoints
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    """GET /health must return status and database info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_root_returns_app_info(client: AsyncClient) -> None:
    """GET / must return application metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_openapi_schema_accessible(client: AsyncClient) -> None:
    """GET /openapi.json must return a valid OpenAPI schema."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
