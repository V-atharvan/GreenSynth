"""
GreenSynth Analytics — Integration Tests: Project 7 Recommendation Engine Pipeline
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHARACTERIZATIONS_API = "/api/v1/characterizations"
DOE_API = "/api/v1/doe"
ML_API = "/api/v1/ml"
RECOMMENDATIONS_API = "/api/v1/recommendations"


@pytest.mark.asyncio
async def test_full_project7_recommendation_pipeline(client: AsyncClient):
    # 1. Create Project 7
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": "P7-REC",
            "name": "Project 7 CuO Mulberry Recommendation",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    proj_id = p_resp.json()["id"]

    # 2. Parameter Definitions
    pd1_resp = await client.post(
        f"{PROJECTS_API}/{proj_id}/parameters",
        json={
            "parameter_code": "substrate_temperature",
            "parameter_name": "Substrate Temperature",
            "unit": "degC",
            "data_type": "NUMBER",
            "min_value": 200.0,
            "max_value": 500.0,
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
            "min_value": 1.0,
            "max_value": 5.0,
            "required": True,
        },
    )
    pdef2_id = pd2_resp.json()["id"]

    # 3. Create 6 Completed Experiments
    temp_vals = [250.0, 300.0, 350.0, 400.0, 450.0, 500.0]
    spray_vals = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    exp_ids = []

    for idx in range(6):
        e_resp = await client.post(
            f"{EXPERIMENTS_API}/",
            json={
                "project_id": proj_id,
                "experiment_code": f"EXP-P7-00{idx + 1}",
                "title": f"P7 Exp {idx + 1}",
                "status": "COMPLETED",
            },
        )
        assert e_resp.status_code == 201
        exp_id = e_resp.json()["id"]
        exp_ids.append(exp_id)

        await client.post(
            f"{EXPERIMENTS_API}/{exp_id}/parameters",
            json={
                "parameters": [
                    {"parameter_definition_id": pdef1_id, "value": str(temp_vals[idx]), "unit": "degC"},
                    {"parameter_definition_id": pdef2_id, "value": str(spray_vals[idx]), "unit": "mL/min"},
                ]
            },
        )

        s_resp = await client.post(
            f"{SAMPLES_API}/",
            json={
                "experiment_id": exp_id,
                "sample_code": f"SMP-P7-00{idx + 1}",
                "name": f"P7 Sample {idx + 1}",
                "material": "CuO",
            },
        )
        smp_id = s_resp.json()["id"]

        c_resp = await client.post(f"{CHARACTERIZATIONS_API}", json={"sample_id": smp_id, "technique": "ELECTRICAL"})
        char_id = c_resp.json()["id"]

        iv_rows = [f"voltage,current\n-2.0,-0.02\n-1.0,-0.01\n0.0,0.0\n1.0,0.01\n2.0,0.02\n3.0,{0.03 + idx * 0.005:.4f}\n"]
        file_bytes = "".join(iv_rows).encode("utf-8")
        await client.post(f"{CHARACTERIZATIONS_API}/{char_id}/files", files={"file": (f"iv_p7_{idx}.csv", file_bytes, "text/csv")})

        await client.post(
            f"{CHARACTERIZATIONS_API}/{char_id}/electrical/analyze",
            json={
                "geometry": {"geometry_type": "RECTANGULAR_BAR", "length": 1.0, "width": 0.5, "thickness": 0.02},
                "units": {"voltage_unit": "V", "current_unit": "A", "length_unit": "cm"},
            },
        )

    # 4. Create ML Dataset & Train Model
    ds_resp = await client.post(
        f"{ML_API}/datasets",
        json={
            "project_id": proj_id,
            "name": "P7 CuO Dataset v1",
            "target_property": "Electrical Conductivity",
            "target_type": "CALCULATED",
            "target_unit": "S/cm",
            "features": [
                {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "degC"},
                {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
            ],
            "experiment_ids": exp_ids,
        },
    )
    assert ds_resp.status_code == 201
    dataset_id = ds_resp.json()["id"]

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

    # 5. Create Optimization Objective
    obj_resp = await client.post(
        "/api/v1/objectives",
        json={
            "project_id": proj_id,
            "name": "Maximize P7 Conductivity",
            "target_property": "Electrical Conductivity",
            "direction": "MAXIMIZE",
            "unit": "S/cm",
            "constraints": [
                {"parameter": "substrate_temperature", "operator": "<=", "value": 450.0},
                {"parameter": "substrate_temperature", "operator": ">=", "value": 250.0},
            ],
        },
    )
    assert obj_resp.status_code == 201
    objective_id = obj_resp.json()["id"]

    # 6. Attempt Recommendation with UNVALIDATED Model (Status: TRAINED) -> MUST BE BLOCKED
    unval_resp = await client.post(
        f"{RECOMMENDATIONS_API}/generate",
        json={
            "project_id": proj_id,
            "objective_id": objective_id,
            "model_id": model_id,  # Still status TRAINED!
            "candidate_count": 5,
        },
    )
    assert unval_resp.status_code in (400, 422)
    detail_str = str(unval_resp.json().get("detail") or unval_resp.json().get("message") or "")
    assert "status" in detail_str.lower(), f"Expected status in error message, got {detail_str}"

    # 7. Approve Model (Setting status to PRODUCTION_CANDIDATE)
    await client.post(f"{ML_API}/models/{model_id}/approve", json={"notes": "Approved for P7 recommendations"})

    # 8. Generate Candidate Recommendations
    rec_resp = await client.post(
        f"{RECOMMENDATIONS_API}/generate",
        json={
            "project_id": proj_id,
            "objective_id": objective_id,
            "model_id": model_id,
            "candidate_count": 5,
            "ranking_method": "BALANCED",
            "random_seed": 42,
        },
    )
    assert rec_resp.status_code == 201
    rec_data = rec_resp.json()
    assert rec_data["status"] == "GENERATED"
    candidates = rec_data["candidates"]
    assert len(candidates) > 0

    top_cand = candidates[0]
    assert top_cand["rank"] == 1
    assert top_cand["applicability_status"] in ("IN_DOMAIN", "NEAR_BOUNDARY", "OUT_OF_DOMAIN")
    assert top_cand["evidence_level"] in ("HIGH", "MODERATE", "LOW")
    assert "#1" in top_cand["explanation"]

    # 9. Researcher Approval of Candidate #1
    app_resp = await client.post(f"{RECOMMENDATIONS_API}/candidates/{top_cand['id']}/approve")
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "APPROVED"

    # 10. Researcher Modification of Candidate #2
    if len(candidates) > 1:
        cand2 = candidates[1]
        mod_resp = await client.post(
            f"{RECOMMENDATIONS_API}/candidates/{cand2['id']}/modify",
            json={
                "modified_parameter_set": {"substrate_temperature": 365.0, "spray_rate": 2.8},
                "modification_reason": "Researcher adjusted temperature to match available spray nozzle heater.",
            },
        )
        assert mod_resp.status_code == 200
        mod_data = mod_resp.json()
        assert mod_data["status"] == "MODIFIED"
        assert mod_data["modified_parameter_set"]["substrate_temperature"] == 365.0
        assert mod_data["parameter_set"] != mod_data["modified_parameter_set"]  # Original preserved!

    # 11. Create PLANNED Experiment from Candidate #1
    exp_create_resp = await client.post(f"{RECOMMENDATIONS_API}/candidates/{top_cand['id']}/create-experiment")
    assert exp_create_resp.status_code == 201
    exp_create_data = exp_create_resp.json()
    assert exp_create_data["status"] == "PLANNED"
    assert "EXP-REC-" in exp_create_data["experiment_code"]
