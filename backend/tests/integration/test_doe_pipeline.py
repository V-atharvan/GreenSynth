"""
GreenSynth Analytics — Phase 14 DOE End-to-End Pipeline Integration Test
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_doe_project7_cuo_pipeline(client: AsyncClient, db_session: AsyncSession):
    """End-to-end integration test for Project 7 CuO Spray Pyrolysis DOE workflow."""

    # 1. Create Demonstration Project 7
    proj = Project(
        id=uuid.uuid4(),
        project_code="PROJ-007",
        name="Project 7 - Phytochemical CuO Thin Film DOE Synthesis",
        description="Spray pyrolysis synthesis of CuO using Mulberry leaf extract",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(proj)
    await db_session.commit()

    # 2. Preview DOE Workload via API
    doe_payload = {
        "project_id": str(proj.id),
        "name": "CuO Spray Pyrolysis Full Factorial DOE",
        "description": "Full factorial study of substrate temperature, spray rate, and precursor concentration",
        "research_question": "How do substrate temperature and spray rate interact for CuO thin film conductivity?",
        "design_method": "FULL_FACTORIAL",
        "factors": [
            {
                "parameter_code": "substrate_temperature",
                "name": "Substrate Temperature",
                "factor_type": "CONTINUOUS",
                "role": "CONTROLLABLE",
                "lower_bound": 300,
                "upper_bound": 400,
                "unit": "°C",
                "levels": 2,
            },
            {
                "parameter_code": "spray_rate",
                "name": "Spray Rate",
                "factor_type": "CONTINUOUS",
                "role": "CONTROLLABLE",
                "lower_bound": 2.0,
                "upper_bound": 5.0,
                "unit": "mL/min",
                "levels": 2,
            },
            {
                "parameter_code": "precursor_concentration",
                "name": "Precursor Concentration",
                "factor_type": "CONTINUOUS",
                "role": "CONTROLLABLE",
                "lower_bound": 0.05,
                "upper_bound": 0.15,
                "unit": "M",
                "levels": 2,
            },
        ],
        "responses": [
            {
                "property_name": "Electrical Conductivity",
                "unit": "S/cm",
                "direction": "MAXIMIZE",
                "weight": 1.0,
            }
        ],
        "replicates": 1,
        "center_points": 0,
        "random_seed": 42,
        "randomize_run_order": True,
    }

    res_prev = await client.post("/api/v1/doe/preview", json=doe_payload)
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["base_runs"] == 8
    assert prev_data["total_runs"] == 8

    # 3. Create DOE and generate proposed experiments
    res_gen = await client.post("/api/v1/doe", json=doe_payload)
    assert res_gen.status_code == 201
    gen_data = res_gen.json()
    doe_id = gen_data["doe"]["id"]
    assert gen_data["doe"]["status"] == "GENERATED"
    assert gen_data["quality_report"]["total_proposed_runs"] == 8

    # 4. Fetch proposed experiment runs
    res_runs = await client.get(f"/api/v1/doe/{doe_id}/proposed-experiments")
    assert res_runs.status_code == 200
    runs = res_runs.json()
    assert len(runs) == 8
    first_run_id = runs[0]["id"]
    assert runs[0]["status"] == "PROPOSED"

    # 5. Approve DOE Study & Lock V1
    res_app = await client.post(f"/api/v1/doe/{doe_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # 6. Convert approved PROPOSED run into PLANNED experiment
    res_conv = await client.post(f"/api/v1/doe/proposed-experiments/{first_run_id}/convert")
    assert res_conv.status_code == 201
    exp_data = res_conv.json()
    assert exp_data["status"] == "PLANNED"
    assert "EXP-DOE-" in exp_data["experiment_code"]

    # 7. Compute DOE Statistical Effect Analysis
    res_an = await client.get(f"/api/v1/doe/{doe_id}/analysis?response_property=Electrical+Conductivity")
    assert res_an.status_code == 200
    analysis = res_an.json()
    assert analysis["doe_id"] == doe_id
    assert "main_effects" in analysis
