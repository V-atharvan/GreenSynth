"""
GreenSynth Analytics — Phase 15 Evidence & Advanced Statistics Integration Test
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Dataset
from app.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_evidence_project7_pipeline(client: AsyncClient, db_session: AsyncSession):
    """End-to-end integration test for Project 7 Advanced Evidence Workflow."""

    # 1. Create Demonstration Project 7 & Dataset
    proj = Project(
        id=uuid.uuid4(),
        project_code=f"PROJ-007-EV-{uuid.uuid4().hex[:4]}",
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

    ds = Dataset(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="PROJECT7-SPRAY-PYROLYSIS-DATASET",
        version="v1",
        sample_ids=[str(uuid.uuid4()) for _ in range(8)],
        variables=["substrate_temperature", "spray_rate", "conductivity_s_cm"],
    )
    db_session.add(ds)
    await db_session.commit()

    # 2. Create Dataset Version Snapshot via API
    res_dv = await client.post(f"/api/v1/statistics/datasets?dataset_id={ds.id}&version_label=v1.0")
    assert res_dv.status_code == 201
    dv_data = res_dv.json()
    dv_id = dv_data["id"]
    assert dv_data["version"] == "v1.0"

    # 3. Compute Descriptive Statistics via API
    res_desc = await client.post(
        "/api/v1/statistics/descriptive?variable_name=substrate_temperature&unit=%C2%B0C",
        json=[300.0, 350.0, 400.0, 350.0, 300.0, 400.0],
    )
    assert res_desc.status_code == 200
    desc_data = res_desc.json()
    assert desc_data["sample_size_n"] == 6
    assert desc_data["mean"] == 350.0

    # 4. Fit Regression Model & Diagnostics via API
    rows = [
        {"substrate_temperature": 300.0, "spray_rate": 2.0, "conductivity_s_cm": 1.2},
        {"substrate_temperature": 300.0, "spray_rate": 5.0, "conductivity_s_cm": 2.1},
        {"substrate_temperature": 400.0, "spray_rate": 2.0, "conductivity_s_cm": 4.5},
        {"substrate_temperature": 400.0, "spray_rate": 5.0, "conductivity_s_cm": 5.8},
    ]
    res_reg = await client.post("/api/v1/statistics/regression?model_type=INTERACTION&include_interaction=true", json=rows)
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["r_squared"] > 0.95

    # 5. Create Evidence Record via API
    evidence_payload = {
        "dataset_version_id": dv_id,
        "statement": "Within the analyzed Project 7 dataset (N=8), electrical conductivity showed a statistically detectable positive association with substrate temperature.",
        "evidence_type": "ASSOCIATION",
        "variables": ["substrate_temperature", "conductivity_s_cm"],
        "sample_size": 8,
        "statistical_method": "Pearson Correlation",
        "effect_estimate": 0.89,
        "uncertainty": 0.05,
        "limitations": ["Small sample size N=8"],
    }
    res_ev = await client.post("/api/v1/evidence", json=evidence_payload)
    assert res_ev.status_code == 201
    ev_data = res_ev.json()
    ev_id = ev_data["id"]
    assert ev_data["status"] == "DRAFT"
    assert ev_data["evidence_score"] >= 70.0

    # 6. Approve Evidence Record via API
    res_app = await client.post(f"/api/v1/evidence/{ev_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # 7. Evaluate ML-Ready Quality Gate via API
    res_gate = await client.get(f"/api/v1/statistics/readiness-gates/{dv_id}?sample_size=10")
    assert res_gate.status_code == 200
    gate_data = res_gate.json()
    assert gate_data["is_ml_ready"] is True
    assert "software validation quality gates" in gate_data["disclaimer"]
