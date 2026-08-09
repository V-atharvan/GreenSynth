"""
GreenSynth Analytics — Integration Tests: Samples API
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"


async def create_project_and_experiment(
    client: AsyncClient, suffix: str
) -> tuple[str, str]:
    """Helper: create project + experiment, return (project_id, experiment_id)."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-SAMPLE-{suffix}",
            "name": f"Sample Test Project {suffix}",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    project_id = p_resp.json()["id"]

    e_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": f"EXP-SAMPLE-{suffix}",
            "title": f"Experiment {suffix}",
            "status": "PLANNED",
        },
    )
    assert e_resp.status_code == 201
    return project_id, e_resp.json()["id"]


@pytest.mark.asyncio
async def test_create_sample(client: AsyncClient) -> None:
    """POST /samples creates and returns a sample."""
    _, exp_id = await create_project_and_experiment(client, "CREATE")

    resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": exp_id,
            "sample_code": "S-CREATE-001",
            "name": "Sample Create Test",
            "material": "CuO",
            "status": "PREPARED",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sample_code"] == "S-CREATE-001"
    assert data["experiment_id"] == exp_id
    assert data["status"] == "PREPARED"


@pytest.mark.asyncio
async def test_create_sample_invalid_experiment(client: AsyncClient) -> None:
    """POST /samples with unknown experiment_id returns 404."""
    resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": "00000000-0000-0000-0000-000000000000",
            "sample_code": "S-ORPHAN",
            "name": "Orphan Sample",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_samples_filter_by_experiment(client: AsyncClient) -> None:
    """GET /samples?experiment_id=... returns only that experiment's samples."""
    _, exp_id = await create_project_and_experiment(client, "FILTER")

    await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": exp_id,
            "sample_code": "S-FILTER-001",
            "name": "Filtered Sample",
        },
    )

    resp = await client.get(f"{SAMPLES_API}/?experiment_id={exp_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(s["experiment_id"] == exp_id for s in data)


@pytest.mark.asyncio
async def test_project_experiment_sample_chain(client: AsyncClient) -> None:
    """
    Verify the full Project → Experiment → Sample relationship chain.

    This test validates that the core scientific traceability chain
    works correctly at the database level.
    """
    # Create project
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": "P-CHAIN-TEST",
            "name": "Chain Test Project",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    project_id = p_resp.json()["id"]

    # Create experiment under project
    e_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": project_id,
            "experiment_code": "EXP-CHAIN-001",
            "title": "Chain Experiment",
            "status": "IN_PROGRESS",
        },
    )
    assert e_resp.status_code == 201
    exp_id = e_resp.json()["id"]

    # Create two samples under experiment
    for i in range(1, 3):
        s_resp = await client.post(
            f"{SAMPLES_API}/",
            json={
                "experiment_id": exp_id,
                "sample_code": f"S-CHAIN-00{i}",
                "name": f"Chain Sample {i}",
                "material": "CuO",
            },
        )
        assert s_resp.status_code == 201

    # Verify samples are linked to experiment
    samples_resp = await client.get(f"{SAMPLES_API}/?experiment_id={exp_id}")
    assert samples_resp.status_code == 200
    samples = samples_resp.json()
    assert len(samples) == 2
    assert all(s["experiment_id"] == exp_id for s in samples)

    # Verify experiment links to project
    exp_detail_resp = await client.get(f"{EXPERIMENTS_API}/{exp_id}")
    assert exp_detail_resp.status_code == 200
    exp_data = exp_detail_resp.json()
    assert exp_data["project"]["id"] == project_id


@pytest.mark.asyncio
async def test_update_sample_status(client: AsyncClient) -> None:
    """PUT /samples/{id} updates sample status."""
    _, exp_id = await create_project_and_experiment(client, "UPSTAT")
    create_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": exp_id,
            "sample_code": "S-UPSTAT-001",
            "name": "Status Update Sample",
            "status": "PREPARED",
        },
    )
    sample_id = create_resp.json()["id"]

    resp = await client.put(
        f"{SAMPLES_API}/{sample_id}",
        json={"status": "UNDER_ANALYSIS"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "UNDER_ANALYSIS"
