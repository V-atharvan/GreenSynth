"""
GreenSynth Analytics — Integration Tests: Model & Experimental Validation Pipeline
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHARACTERIZATIONS_API = "/api/v1/characterizations"
ML_API = "/api/v1/ml"
VALIDATION_API = "/api/v1/validation"


@pytest.mark.asyncio
async def test_full_validation_pipeline(client: AsyncClient):
    # 1. Create Project
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": "P11-VAL",
            "name": "Phase 11 Validation Test Project",
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
    pdef2_id = pd2_resp.json()["id"]

    # 3. Create 7 Completed Experiments (6 for training, 1 holdout)
    temp_vals = [250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0]
    spray_vals = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    exp_ids = []
    smp_ids = []

    for idx in range(7):
        e_resp = await client.post(
            f"{EXPERIMENTS_API}/",
            json={
                "project_id": proj_id,
                "experiment_code": f"EXP-VAL-00{idx + 1}",
                "title": f"Validation Exp {idx + 1}",
                "status": "COMPLETED",
            },
        )
        assert e_resp.status_code == 201
        exp_id = e_resp.json()["id"]
        exp_ids.append(exp_id)

        # Record parameters
        await client.post(
            f"{EXPERIMENTS_API}/{exp_id}/parameters",
            json={
                "parameters": [
                    {"parameter_definition_id": pdef1_id, "value": str(temp_vals[idx]), "unit": "degC"},
                    {"parameter_definition_id": pdef2_id, "value": str(spray_vals[idx]), "unit": "mL/min"},
                ]
            },
        )

        # Create Sample
        s_resp = await client.post(
            f"{SAMPLES_API}/",
            json={
                "experiment_id": exp_id,
                "sample_code": f"SMP-VAL-00{idx + 1}",
                "name": f"Sample {idx + 1}",
                "material": "CuO",
            },
        )
        smp_id = s_resp.json()["id"]
        smp_ids.append(smp_id)

        # Create Characterization & Raw File
        c_resp = await client.post(f"{CHARACTERIZATIONS_API}", json={"sample_id": smp_id, "technique": "ELECTRICAL"})
        char_id = c_resp.json()["id"]

        iv_rows = [f"voltage,current\n-2.0,-0.02\n-1.0,-0.01\n0.0,0.0\n1.0,0.01\n2.0,0.02\n3.0,{0.03 + idx * 0.001:.4f}\n"]
        file_bytes = "".join(iv_rows).encode("utf-8")
        await client.post(f"{CHARACTERIZATIONS_API}/{char_id}/files", files={"file": (f"iv_v_{idx}.csv", file_bytes, "text/csv")})

        # Electrical Analyze
        await client.post(
            f"{CHARACTERIZATIONS_API}/{char_id}/electrical/analyze",
            json={
                "geometry": {"geometry_type": "RECTANGULAR_BAR", "length": 1.0, "width": 0.5, "thickness": 0.02},
                "units": {"voltage_unit": "V", "current_unit": "A", "length_unit": "cm"},
            },
        )

    # 4. Create ML Dataset including ONLY first 6 experiments (excluding exp_ids[6])
    ds_resp = await client.post(
        f"{ML_API}/datasets",
        json={
            "project_id": proj_id,
            "name": "CuO Validation Dataset v1",
            "target_property": "Electrical Conductivity",
            "target_type": "CALCULATED",
            "target_unit": "S/cm",
            "features": [
                {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "degC"},
                {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
            ],
            "experiment_ids": exp_ids[:6],  # Explicitly exclude exp_ids[6]
        },
    )
    assert ds_resp.status_code == 201
    dataset_id = ds_resp.json()["id"]

    # 5. Train Model v1
    tr_resp = await client.post(
        f"{ML_API}/training-runs",
        json={
            "dataset_id": dataset_id,
            "model_types": ["LINEAR_REGRESSION"],
            "scaling": "STANDARD",
            "cv_folds": 3,
            "random_seed": 42,
        },
    )
    assert tr_resp.status_code == 201
    models = tr_resp.json()
    model_id = models[0]["id"]

    # Approve Model v1
    await client.post(f"{ML_API}/models/{model_id}/approve", json={"notes": "Approved for validation"})

    # 6. Create Validation Criterion
    crit_resp = await client.post(
        f"{VALIDATION_API}/criteria",
        json={
            "property_name": "Electrical Conductivity",
            "metric": "ABSOLUTE_ERROR",
            "threshold": 1.0,
            "unit": "S/cm",
            "comparison_operator": "<=",
            "description": "Max acceptable conductivity absolute error <= 1.0 S/cm",
        },
    )
    assert crit_resp.status_code == 201
    criterion_id = crit_resp.json()["id"]

    # 7. Execute Level 2 Holdout Validation on experiment #7 (exp_ids[6])
    hold_resp = await client.post(
        f"{VALIDATION_API}/holdout",
        json={
            "model_id": model_id,
            "experiment_id": exp_ids[6],
            "sample_id": smp_ids[6],
            "criterion_id": criterion_id,
            "researcher": "Dr. Validation Engineer",
            "notes": "Validating holdout experiment 7",
        },
    )
    assert hold_resp.status_code == 201
    hold_data = hold_resp.json()
    assert hold_data["status"] == "COMPLETED"
    assert hold_data["absolute_error"] >= 0.0

    # 8. Attempt Holdout Validation on a TRAINED experiment (exp_ids[0]) -> MUST FAIL WITH LEAKAGE BLOCK
    leak_resp = await client.post(
        f"{VALIDATION_API}/holdout",
        json={
            "model_id": model_id,
            "experiment_id": exp_ids[0],  # Was in training set!
            "sample_id": smp_ids[0],
        },
    )
    assert leak_resp.status_code == 201
    assert leak_resp.json()["status"] == "FAILED_LEAKAGE"

    # 9. Generate Prediction & Approve Prospective Experiment
    pred_resp = await client.post(
        f"{ML_API}/models/{model_id}/predict",
        json={
            "input_parameters": {"substrate_temperature": 350.0, "spray_rate": 2.8},
            "notes": "Candidate synthesis prediction for prospective validation",
        },
    )
    assert pred_resp.status_code == 201
    prediction_id = pred_resp.json()["id"]

    prosp_resp = await client.post(
        f"{VALIDATION_API}/prospective",
        json={
            "prediction_id": prediction_id,
            "project_id": proj_id,
            "researcher": "Dr. Validation Engineer",
            "notes": "Approved for physical lab synthesis",
        },
    )
    assert prosp_resp.status_code == 201
    prospective_id = prosp_resp.json()["id"]

    # 10. Link Prospective Result to Physical Characterization (use sample #3)
    link_resp = await client.post(
        f"{VALIDATION_API}/prospective/{prospective_id}/link-result?"
        f"laboratory_experiment_id={exp_ids[2]}&sample_id={smp_ids[2]}&criterion_id={criterion_id}&measurement_uncertainty=0.1"
    )
    assert link_resp.status_code == 201
    vr_data = link_resp.json()
    assert vr_data["validation_type"] == "PROSPECTIVE"
    assert vr_data["criterion_result"] in ("SATISFIED", "NOT_SATISFIED")

    # 11. Query Model Performance History
    hist_resp = await client.get(f"/api/v1/models/{model_id}/performance-history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["n_experimental_validations"] >= 1
    assert hist_data["experimental_mae"] is not None

    # 12. Retrain Model (Creating Dataset v2 & Model v2 while Model v1 remains unchanged)
    retrain_resp = await client.post(
        f"/api/v1/models/{model_id}/retrain",
        json={"notes": "Incorporating new validation records into Model v2"},
    )
    assert retrain_resp.status_code == 201
    new_models = retrain_resp.json()
    assert len(new_models) == 1
    assert new_models[0]["version"] == "2.0"
    assert new_models[0]["id"] != model_id
