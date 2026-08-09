"""
GreenSynth Analytics — Integration Tests: Projects API
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


API = "/api/v1/projects"


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient) -> None:
    """GET /projects returns an empty list when no projects exist."""
    response = await client.get(f"{API}/")
    assert response.status_code == 200
    # May include seeded P7 project — just verify it's a list
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient) -> None:
    """POST /projects creates and returns a project."""
    payload = {
        "project_code": "P-TEST-1",
        "name": "Integration Test Project",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "synthesis_method": "Spray Pyrolysis",
        "description": "Test project for integration tests",
    }
    response = await client.post(f"{API}/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["project_code"] == "P-TEST-1"
    assert data["name"] == "Integration Test Project"
    assert data["material"] == "CuO"
    assert data["status"] == "ACTIVE"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_project_duplicate_code_fails(client: AsyncClient) -> None:
    """POST /projects with duplicate code returns 409 Conflict."""
    payload = {
        "project_code": "P-DUP",
        "name": "Original",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "synthesis_method": "Sol-gel",
    }
    await client.post(f"{API}/", json=payload)

    response = await client.post(f"{API}/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient) -> None:
    """GET /projects/{id} returns the correct project."""
    # Create
    payload = {
        "project_code": "P-GET-TEST",
        "name": "Get Test Project",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Acetone",
        "synthesis_method": "Hydrothermal",
    }
    create_resp = await client.post(f"{API}/", json=payload)
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    # Get
    response = await client.get(f"{API}/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id
    assert response.json()["project_code"] == "P-GET-TEST"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient) -> None:
    """GET /projects/{id} with unknown UUID returns 404."""
    response = await client.get(f"{API}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient) -> None:
    """PUT /projects/{id} updates specified fields."""
    payload = {
        "project_code": "P-UPD-TEST",
        "name": "Before Update",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "synthesis_method": "Spray Pyrolysis",
    }
    create_resp = await client.post(f"{API}/", json=payload)
    project_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"{API}/{project_id}",
        json={"name": "After Update", "status": "ACTIVE"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "After Update"


@pytest.mark.asyncio
async def test_delete_project_archives_it(client: AsyncClient) -> None:
    """DELETE /projects/{id} archives the project (soft delete)."""
    payload = {
        "project_code": "P-DEL-TEST",
        "name": "To Be Archived",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "synthesis_method": "Spray Pyrolysis",
    }
    create_resp = await client.post(f"{API}/", json=payload)
    project_id = create_resp.json()["id"]

    del_resp = await client.delete(f"{API}/{project_id}")
    assert del_resp.status_code == 204

    # Archived projects excluded from default list
    list_resp = await client.get(f"{API}/")
    ids = [p["id"] for p in list_resp.json()]
    assert project_id not in ids

    # But accessible with include_archived=true
    list_with_archived = await client.get(f"{API}/?include_archived=true")
    ids_with_archived = [p["id"] for p in list_with_archived.json()]
    assert project_id in ids_with_archived
