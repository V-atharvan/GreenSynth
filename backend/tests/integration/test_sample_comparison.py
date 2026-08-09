"""
GreenSynth Analytics — Integration Tests: Sample Comparison & Statistical Analysis Pipeline
"""

from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient

from app.models.analysis import AnalysisStatus

PROJECTS_API = "/api/v1/projects/"
EXPERIMENTS_API = "/api/v1/experiments/"
SAMPLES_API = "/api/v1/samples/"
CHARACTERIZATIONS_API = "/api/v1/characterizations"
ANALYTICS_API = "/api/v1/analytics"


@pytest.mark.asyncio
async def test_full_sample_comparison_and_statistics_pipeline(client: AsyncClient) -> None:
    """Full integration pipeline testing dataset creation, comparison table with provenance, and statistical runs."""
    # 1. Create Project
    p_resp = await client.post(
        PROJECTS_API,
        json={
            "project_code": "P8-STAT",
            "name": "Phase 8 Statistics Test Project",
            "description": "Multi-sample statistical comparison study",
            "material": "ZnO",
            "extract": "Neem Extract",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    proj_id = p_resp.json()["id"]

    # 2. Create Parameter Definitions
    pd1_resp = await client.post(
        f"{ANALYTICS_API.replace('/analytics', '')}/projects/{proj_id}/parameters",
        json={"parameter_code": "substrate_temperature", "parameter_name": "Substrate Temperature", "unit": "°C", "data_type": "NUMBER", "required": True},
    )
    assert pd1_resp.status_code == 201
    pdef1_id = pd1_resp.json()["id"]

    # 3. Create Experiment 1
    e1_resp = await client.post(
        EXPERIMENTS_API,
        json={
            "project_id": proj_id,
            "experiment_code": "EXP-STAT-1",
            "title": "Low Temp Synthesis",
        },
    )
    assert e1_resp.status_code == 201
    exp1_id = e1_resp.json()["id"]
    await client.post(
        f"{EXPERIMENTS_API}{exp1_id}/parameters",
        json={"parameters": [{"parameter_definition_id": pdef1_id, "value": "300"}]},
    )

    # Create Sample S1
    s1_resp = await client.post(
        SAMPLES_API,
        json={"experiment_id": exp1_id, "sample_code": "S-STAT-001", "name": "Sample 300C"},
    )
    assert s1_resp.status_code == 201
    s1_id = s1_resp.json()["id"]

    # 4. Create Experiment 2
    e2_resp = await client.post(
        EXPERIMENTS_API,
        json={
            "project_id": proj_id,
            "experiment_code": "EXP-STAT-2",
            "title": "High Temp Synthesis",
        },
    )
    assert e2_resp.status_code == 201
    exp2_id = e2_resp.json()["id"]
    await client.post(
        f"{EXPERIMENTS_API}{exp2_id}/parameters",
        json={"parameters": [{"parameter_definition_id": pdef1_id, "value": "400"}]},
    )
    exp2_id = e2_resp.json()["id"]

    # Create Sample S2
    s2_resp = await client.post(
        SAMPLES_API,
        json={"experiment_id": exp2_id, "sample_code": "S-STAT-002", "name": "Sample 400C"},
    )
    assert s2_resp.status_code == 201
    s2_id = s2_resp.json()["id"]

    # Create Sample S3
    s3_resp = await client.post(
        SAMPLES_API,
        json={"experiment_id": exp2_id, "sample_code": "S-STAT-003", "name": "Sample 400C Replicate"},
    )
    assert s3_resp.status_code == 201
    s3_id = s3_resp.json()["id"]

    # 5. Create Electrical Characterizations & upload I-V curve files
    c1_resp = await client.post(
        CHARACTERIZATIONS_API,
        json={"sample_id": s1_id, "technique": "ELECTRICAL", "instrument_name": "Keithely 2400"},
    )
    c1_id = c1_resp.json()["id"]
    await client.post(
        f"{CHARACTERIZATIONS_API}/{c1_id}/files",
        files={"file": ("s1_iv.csv", b"Voltage (V),Current (A)\n-2.0,-0.002\n-1.0,-0.001\n0.0,0.0\n1.0,0.001\n2.0,0.002\n", "text/csv")},
    )
    # Run electrical analysis to generate calculated property
    await client.post(f"{CHARACTERIZATIONS_API}/{c1_id}/electrical/analyze", json={"geometry": {"length": 1.0, "width": 1.0, "thickness": 0.0001}})

    c2_resp = await client.post(
        CHARACTERIZATIONS_API,
        json={"sample_id": s2_id, "technique": "ELECTRICAL", "instrument_name": "Keithely 2400"},
    )
    c2_id = c2_resp.json()["id"]
    await client.post(
        f"{CHARACTERIZATIONS_API}/{c2_id}/files",
        files={"file": ("s2_iv.csv", b"Voltage (V),Current (A)\n-2.0,-0.010\n-1.0,-0.005\n0.0,0.0\n1.0,0.005\n2.0,0.010\n", "text/csv")},
    )
    await client.post(f"{CHARACTERIZATIONS_API}/{c2_id}/electrical/analyze", json={"geometry": {"length": 1.0, "width": 1.0, "thickness": 0.0001}})

    c3_resp = await client.post(
        CHARACTERIZATIONS_API,
        json={"sample_id": s3_id, "technique": "ELECTRICAL", "instrument_name": "Keithely 2400"},
    )
    c3_id = c3_resp.json()["id"]
    await client.post(
        f"{CHARACTERIZATIONS_API}/{c3_id}/files",
        files={"file": ("s3_iv.csv", b"Voltage (V),Current (A)\n-2.0,-0.012\n-1.0,-0.006\n0.0,0.0\n1.0,0.006\n2.0,0.012\n", "text/csv")},
    )
    await client.post(f"{CHARACTERIZATIONS_API}/{c3_id}/electrical/analyze", json={"geometry": {"length": 1.0, "width": 1.0, "thickness": 0.0001}})

    # 6. Create Dataset Definition
    ds_resp = await client.post(
        f"{ANALYTICS_API}/datasets",
        json={
            "project_id": proj_id,
            "name": "Temperature vs Electrical Conductivity Study",
            "description": "Multi-sample comparative dataset for ZnO films",
            "sample_ids": [s1_id, s2_id, s3_id],
            "variables": ["substrate_temperature", "Electrical Conductivity"],
        },
    )
    assert ds_resp.status_code == 201
    dataset_id = ds_resp.json()["id"]

    # 7. Fetch Comparison Table & Verify Provenance
    tbl_resp = await client.get(f"{ANALYTICS_API}/datasets/{dataset_id}/comparison-table")
    assert tbl_resp.status_code == 200
    tbl_data = tbl_resp.json()
    assert tbl_data["total_samples"] == 3
    assert len(tbl_data["rows"]) == 3

    # Check cell status: substrate_temperature => MEASURED, Electrical Conductivity => CALCULATED
    row1 = next(r for r in tbl_data["rows"] if r["sample_code"] == "S-STAT-001")
    assert row1["cells"]["substrate_temperature"]["status"] == "MEASURED"
    assert row1["cells"]["substrate_temperature"]["value"] == 300.0
    assert row1["cells"]["Electrical Conductivity"]["status"] == "CALCULATED"

    # 8. Run Descriptive Statistics
    desc_resp = await client.post(
        f"{ANALYTICS_API}/datasets/{dataset_id}/statistics",
        json={"analysis_type": "DESCRIPTIVE"},
    )
    assert desc_resp.status_code == 201
    desc_data = desc_resp.json()
    assert desc_data["analysis_type"] == "DESCRIPTIVE"

    # 9. Run Pearson Correlation (substrate_temperature vs Electrical Conductivity)
    corr_resp = await client.post(
        f"{ANALYTICS_API}/datasets/{dataset_id}/statistics",
        json={"analysis_type": "CORRELATION", "x_variable": "substrate_temperature", "y_variable": "Electrical Conductivity"},
    )
    assert corr_resp.status_code == 201
    corr_data = corr_resp.json()
    assert corr_data["analysis_type"] == "CORRELATION"
    assert "pearson_r" in corr_data["results_json"]

    # 10. Run Linear Regression
    reg_resp = await client.post(
        f"{ANALYTICS_API}/datasets/{dataset_id}/statistics",
        json={"analysis_type": "REGRESSION", "x_variable": "substrate_temperature", "y_variable": "Electrical Conductivity"},
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["analysis_type"] == "REGRESSION"
    assert "r_squared" in reg_data["results_json"]

    # 11. Export Dataset CSV
    exp_resp = await client.get(f"{ANALYTICS_API}/datasets/{dataset_id}/export")
    assert exp_resp.status_code == 200
    assert "text/csv" in exp_resp.headers["content-type"]
    csv_text = exp_resp.text
    assert "Sample Code" in csv_text
    assert "S-STAT-001" in csv_text
