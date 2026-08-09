"""
GreenSynth Analytics — Integration Tests: Parameters API
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
PARAMS_API = "/api/v1"


async def setup_project_and_experiment(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create project and experiment."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-PARAM-{suffix}",
            "name": f"Param Test Project {suffix}",
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
            "experiment_code": f"EXP-PARAM-{suffix}",
            "title": f"Param Test Experiment {suffix}",
            "status": "PLANNED",
        },
    )
    assert e_resp.status_code == 201
    return project_id, e_resp.json()["id"]


@pytest.mark.asyncio
async def test_create_and_get_parameter_definitions(client: AsyncClient) -> None:
    """Create a parameter definition for a project and retrieve it."""
    project_id, _ = await setup_project_and_experiment(client, "DEF1")

    # Add parameter definition
    create_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "annealing_temp",
            "parameter_name": "Annealing Temperature",
            "description": "Post-deposition thermal annealing temperature",
            "data_type": "NUMBER",
            "unit": "°C",
            "required": True,
            "minimum_value": 100.0,
            "maximum_value": 800.0,
        },
    )
    assert create_resp.status_code == 201
    pdef = create_resp.json()
    assert pdef["parameter_code"] == "annealing_temp"
    assert pdef["unit"] == "°C"
    assert pdef["minimum_value"] == 100.0

    # Retrieve definitions
    list_resp = await client.get(f"{PARAMS_API}/projects/{project_id}/parameters")
    assert list_resp.status_code == 200
    defs = list_resp.json()
    assert len(defs) == 1
    assert defs[0]["parameter_code"] == "annealing_temp"


@pytest.mark.asyncio
async def test_save_experiment_parameters_success(client: AsyncClient) -> None:
    """Save valid synthesis parameter values for an experiment."""
    project_id, exp_id = await setup_project_and_experiment(client, "VAL1")

    # Define parameter
    p_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "temp",
            "parameter_name": "Substrate Temp",
            "data_type": "NUMBER",
            "unit": "°C",
            "required": True,
            "minimum_value": 100.0,
            "maximum_value": 500.0,
        },
    )
    pdef_id = p_resp.json()["id"]

    # Save experiment parameter
    save_resp = await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={
            "parameters": [
                {
                    "parameter_definition_id": pdef_id,
                    "value": "350",
                    "unit": "°C",
                    "notes": "Target temperature achieved",
                }
            ]
        },
    )
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert len(saved) == 1
    assert saved[0]["value"] == "350"
    assert saved[0]["value_numeric"] == 350.0
    assert saved[0]["unit"] == "°C"


@pytest.mark.asyncio
async def test_validation_required_parameter_missing(client: AsyncClient) -> None:
    """Submitting missing required parameter returns 422 Unprocessable Entity."""
    project_id, exp_id = await setup_project_and_experiment(client, "REQMISS")

    await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "req_param",
            "parameter_name": "Required Field",
            "data_type": "TEXT",
            "required": True,
        },
    )

    # Submit empty list
    save_resp = await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={"parameters": []},
    )
    assert save_resp.status_code == 422
    assert "Required parameter 'Required Field' is missing" in save_resp.json()["detail"]


@pytest.mark.asyncio
async def test_validation_invalid_numeric(client: AsyncClient) -> None:
    """Submitting non-numeric text for NUMBER parameter returns 422 error."""
    project_id, exp_id = await setup_project_and_experiment(client, "NONNUM")

    p_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "spray_rate",
            "parameter_name": "Spray Rate",
            "data_type": "NUMBER",
            "unit": "mL/min",
            "required": False,
        },
    )
    pdef_id = p_resp.json()["id"]

    save_resp = await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={
            "parameters": [
                {
                    "parameter_definition_id": pdef_id,
                    "value": "fast",
                }
            ]
        },
    )
    assert save_resp.status_code == 422
    assert "must be a numeric value" in save_resp.json()["detail"]


@pytest.mark.asyncio
async def test_validation_out_of_range(client: AsyncClient) -> None:
    """Submitting value out of allowed range returns 422 error."""
    project_id, exp_id = await setup_project_and_experiment(client, "OOR")

    p_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "temp",
            "parameter_name": "Substrate Temperature",
            "data_type": "NUMBER",
            "unit": "°C",
            "required": False,
            "minimum_value": 100.0,
            "maximum_value": 600.0,
        },
    )
    pdef_id = p_resp.json()["id"]

    save_resp = await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={
            "parameters": [
                {
                    "parameter_definition_id": pdef_id,
                    "value": "850",
                }
            ]
        },
    )
    assert save_resp.status_code == 422
    assert "exceeds the maximum allowed limit" in save_resp.json()["detail"]


@pytest.mark.asyncio
async def test_validation_enum_allowed_values(client: AsyncClient) -> None:
    """Submitting invalid enum option returns 422 error."""
    project_id, exp_id = await setup_project_and_experiment(client, "ENUMVAL")

    p_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "substrate",
            "parameter_name": "Substrate Type",
            "data_type": "ENUM",
            "required": False,
            "allowed_values": ["Glass", "Quartz", "FTO"],
        },
    )
    pdef_id = p_resp.json()["id"]

    save_resp = await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={
            "parameters": [
                {
                    "parameter_definition_id": pdef_id,
                    "value": "Plastic",
                }
            ]
        },
    )
    assert save_resp.status_code == 422
    assert "is invalid. Allowed options" in save_resp.json()["detail"]


@pytest.mark.asyncio
async def test_deactivate_parameter_and_historical_integrity(client: AsyncClient) -> None:
    """
    Deactivating a parameter definition sets status=INACTIVE
    while preserving already recorded experiment parameters.
    """
    project_id, exp_id = await setup_project_and_experiment(client, "HIST")

    # 1. Create parameter definition
    p_resp = await client.post(
        f"{PARAMS_API}/projects/{project_id}/parameters",
        json={
            "parameter_code": "pressure",
            "parameter_name": "Carrier Gas Pressure",
            "data_type": "NUMBER",
            "unit": "kPa",
        },
    )
    pdef_id = p_resp.json()["id"]

    # 2. Record experiment value
    await client.post(
        f"{PARAMS_API}/experiments/{exp_id}/parameters",
        json={"parameters": [{"parameter_definition_id": pdef_id, "value": "150"}]},
    )

    # 3. Deactivate parameter definition
    del_resp = await client.delete(f"{PARAMS_API}/projects/{project_id}/parameters/{pdef_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "INACTIVE"

    # 4. Historical recorded values remain intact and queryable
    get_resp = await client.get(f"{PARAMS_API}/experiments/{exp_id}/parameters")
    assert get_resp.status_code == 200
    saved = get_resp.json()
    assert len(saved) == 1
    assert saved[0]["value"] == "150"
