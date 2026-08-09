"""
GreenSynth Analytics — Integration Tests: ML Dataset, Training, Model Registry & Prediction Pipeline
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHARACTERIZATIONS_API = "/api/v1/characterizations"
ML_API = "/api/v1/ml"


@pytest.mark.asyncio
async def test_full_ml_pipeline(client: AsyncClient):
    # 1. Create Project
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": "P10-ML",
            "name": "Phase 10 ML Integration Test Project",
            "description": "ML pipeline integration study",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    proj_id = p_resp.json()["id"]

    # 2. Create Parameter Definitions
    pd1_resp = await client.post(
        f"{PROJECTS_API}/{proj_id}/parameters",
        json={
            "parameter_code": "substrate_temperature",
            "parameter_name": "Substrate Temperature",
            "unit": "degC",
            "data_type": "NUMBER",
            "required": True,
        },
    )
    assert pd1_resp.status_code == 201
    pdef1_id = pd1_resp.json()["id"]

    pd2_resp = await client.post(
        f"{PROJECTS_API}/{proj_id}/parameters",
        json={
            "parameter_code": "spray_rate",
            "parameter_name": "Spray Rate",
            "unit": "mL/min",
            "data_type": "NUMBER",
            "required": True,
        },
    )
    assert pd2_resp.status_code == 201
    pdef2_id = pd2_resp.json()["id"]

    # 3. Create 6 Completed Experiments, Samples, & Calculated Properties
    temp_vals = [250.0, 280.0, 310.0, 340.0, 370.0, 400.0]
    spray_vals = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    cond_vals = [2.1, 3.5, 5.2, 7.8, 10.4, 13.1]

    for idx in range(6):
        exp_code = f"EXP-ML-00{idx + 1}"
        smp_code = f"SMP-ML-00{idx + 1}"

        # Create Experiment
        e_resp = await client.post(
            f"{EXPERIMENTS_API}/",
            json={
                "project_id": proj_id,
                "experiment_code": exp_code,
                "title": f"ML Training Run {idx + 1}",
                "status": "COMPLETED",
            },
        )
        assert e_resp.status_code == 201
        exp_id = e_resp.json()["id"]

        # Record Parameters
        p_resp = await client.post(
            f"{EXPERIMENTS_API}/{exp_id}/parameters",
            json={
                "parameters": [
                    {
                        "parameter_definition_id": pdef1_id,
                        "value": str(temp_vals[idx]),
                        "unit": "degC",
                    },
                    {
                        "parameter_definition_id": pdef2_id,
                        "value": str(spray_vals[idx]),
                        "unit": "mL/min",
                    },
                ]
            },
        )
        assert p_resp.status_code == 200

        # Create Sample
        s_resp = await client.post(
            f"{SAMPLES_API}/",
            json={
                "experiment_id": exp_id,
                "sample_code": smp_code,
                "name": f"Sample {idx + 1}",
                "material": "CuO",
                "status": "PREPARED",
            },
        )
        assert s_resp.status_code == 201
        smp_id = s_resp.json()["id"]

        # Create Characterization
        c_resp = await client.post(
            f"{CHARACTERIZATIONS_API}",
            json={
                "sample_id": smp_id,
                "technique": "ELECTRICAL",
            },
        )
        assert c_resp.status_code == 201
        char_id = c_resp.json()["id"]

        # Upload raw file
        iv_rows = [f"voltage,current\n-2.0,-0.02\n-1.0,-0.01\n0.0,0.0\n1.0,0.01\n2.0,0.02\n3.0,{0.03 + idx * 0.001:.4f}\n"]
        file_bytes = "".join(iv_rows).encode("utf-8")
        await client.post(
            f"{CHARACTERIZATIONS_API}/{char_id}/files",
            files={"file": (f"iv_{idx}.csv", file_bytes, "text/csv")},
        )

        # Post Analysis Run with Calculated Property (Electrical Conductivity)
        elec_resp = await client.post(
            f"{CHARACTERIZATIONS_API}/{char_id}/electrical/analyze",
            json={
                "geometry": {
                    "geometry_type": "RECTANGULAR_BAR",
                    "length": 1.0,
                    "width": 0.5,
                    "thickness": 0.02,
                },
                "units": {"voltage_unit": "V", "current_unit": "A", "length_unit": "cm"},
            },
        )
        assert elec_resp.status_code == 201

    # 4. Create ML Dataset
    ds_resp = await client.post(
        f"{ML_API}/datasets",
        json={
            "project_id": proj_id,
            "name": "CuO Conductivity Dataset v1",
            "description": "Training dataset for CuO film conductivity",
            "target_property": "Electrical Conductivity",
            "target_type": "CALCULATED",
            "target_unit": "S/cm",
            "features": [
                {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "degC"},
                {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
            ],
        },
    )
    assert ds_resp.status_code == 201
    ds_data = ds_resp.json()
    dataset_id = ds_data["id"]
    assert ds_data["eligible_count"] == 6

    # 5. List Dataset Records
    recs_resp = await client.get(f"{ML_API}/datasets/{dataset_id}/records")
    assert recs_resp.status_code == 200
    records = recs_resp.json()
    assert len(records) == 6
    assert all(r["is_eligible"] for r in records)

    # 6. Train Candidate ML Models
    tr_resp = await client.post(
        f"{ML_API}/training-runs",
        json={
            "dataset_id": dataset_id,
            "model_types": ["MEAN_BASELINE", "LINEAR_REGRESSION", "RIDGE", "RANDOM_FOREST"],
            "scaling": "STANDARD",
            "cv_folds": 3,
            "random_seed": 42,
        },
    )
    assert tr_resp.status_code == 201
    models = tr_resp.json()
    assert len(models) == 4

    linear_model = next(m for m in models if m["model_type"] == "LINEAR_REGRESSION")
    model_id = linear_model["id"]

    # 7. Approve Model (PRODUCTION_CANDIDATE)
    app_resp = await client.post(
        f"{ML_API}/models/{model_id}/approve",
        json={"notes": "Scientifically verified model performance"},
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "PRODUCTION_CANDIDATE"

    # 8. Generate Prediction
    pred_resp = await client.post(
        f"{ML_API}/models/{model_id}/predict",
        json={
            "input_parameters": {
                "substrate_temperature": 320.0,
                "spray_rate": 2.6,
            },
            "notes": "Prediction for optimized synthesis batch",
        },
    )
    assert pred_resp.status_code == 201
    pred_data = pred_resp.json()
    assert pred_data["predicted_property"] == "Electrical Conductivity"
    assert pred_data["predicted_value"] > 0.0
    assert pred_data["applicability_status"] == "VALID"
    assert pred_data["uncertainty_lower"] is not None
    assert pred_data["uncertainty_upper"] is not None

    # 9. List Predictions
    list_pred_resp = await client.get(f"{ML_API}/predictions?model_id={model_id}")
    assert list_pred_resp.status_code == 200
    assert len(list_pred_resp.json()) == 1
