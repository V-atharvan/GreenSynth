"""
GreenSynth Analytics — Integration Tests: Experiments API
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"


async def create_test_project(client: AsyncClient, code: str = "P-EXP-TEST") -> str:
    """Helper: create a project and return its UUID."""
    resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": code,
            "name": f"Project {code}",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_experiment(client: AsyncClient) -> None:
    """POST /experiments creates and returns an experiment."""
    project_id = await create_test_project(client, "P-EXP-1")

    resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-001",
            "title": "First Spray Pyrolysis Run",
            "status": "PLANNED",
            "researcher": "Dr. Test",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["experiment_code"] == "EXP-001"
    assert data["status"] == "PLANNED"
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_create_experiment_invalid_project(client: AsyncClient) -> None:
    """POST /experiments with unknown project_id returns 404."""
    resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": "00000000-0000-0000-0000-000000000000",
            "experiment_code": "EXP-ORPHAN",
            "title": "Orphan Experiment",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_experiments_filter_by_project(client: AsyncClient) -> None:
    """GET /experiments?project_id=... returns only that project's experiments."""
    project_id = await create_test_project(client, "P-FILTER-TEST")

    await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-FILTER-001",
            "title": "Filtered Experiment",
            "status": "PLANNED",
        },
    )

    resp = await client.get(f"{EXPERIMENTS_API}/?project_id={project_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(e["project_id"] == project_id for e in data)


@pytest.mark.asyncio
async def test_get_experiment_with_project(client: AsyncClient) -> None:
    """GET /experiments/{id} returns experiment with nested project data."""
    project_id = await create_test_project(client, "P-NESTED-TEST")
    create_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-NESTED-001",
            "title": "Nested Test",
            "status": "PLANNED",
        },
    )
    exp_id = create_resp.json()["id"]

    resp = await client.get(f"{EXPERIMENTS_API}/{exp_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "project" in data
    assert data["project"]["id"] == project_id


@pytest.mark.asyncio
async def test_update_experiment_status(client: AsyncClient) -> None:
    """PUT /experiments/{id} updates status correctly."""
    project_id = await create_test_project(client, "P-UPSTATUS-TEST")
    create_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-STATUS-001",
            "title": "Status Update Test",
            "status": "PLANNED",
        },
    )
    exp_id = create_resp.json()["id"]

    resp = await client.put(
        f"{EXPERIMENTS_API}/{exp_id}",
        json={"status": "IN_PROGRESS"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_delete_experiment_archives_it(client: AsyncClient) -> None:
    """DELETE /experiments/{id} soft-deletes the experiment."""
    project_id = await create_test_project(client, "P-DELEXP-TEST")
    create_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-DEL-001",
            "title": "To Be Deleted",
            "status": "PLANNED",
        },
    )
    exp_id = create_resp.json()["id"]

    del_resp = await client.delete(f"{EXPERIMENTS_API}/{exp_id}")
    assert del_resp.status_code == 204

    # Should not appear in default list
    list_resp = await client.get(f"{EXPERIMENTS_API}/?project_id={project_id}")
    ids = [e["id"] for e in list_resp.json()]
    assert exp_id not in ids
