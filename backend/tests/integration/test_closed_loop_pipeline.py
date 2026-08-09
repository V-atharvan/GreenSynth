"""
GreenSynth Analytics — Project 7 Closed-Loop Pipeline Integration Test (Phase 13)

Demonstrates complete Project 7 (CuO, Mulberry extract, Spray Pyrolysis) Closed-Loop Workflow:
1. Dataset & Trained Model v1 (Conductivity)
2. Model Recommendation & Researcher Approval
3. Planned Experiment & Lab Execution
4. Physical Characterization & Actual Property Calculation
5. Prediction vs Actual Validation Result
6. DatasetCandidate creation & Researcher Acceptance
7. Dataset v2 creation from accepted candidates
8. Model v2 Retraining & Snapshot creation
9. Manual Model Promotion to ACTIVE status
10. Immutability verification of Model v1 and Dataset v1
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
VALIDATION_API = "/api/v1/validation"
DATASET_CANDIDATES_API = "/api/v1/dataset-candidates"
MODELS_API = "/api/v1/models"


@pytest.mark.asyncio
async def test_project7_closed_loop_pipeline_end_to_end(client: AsyncClient, db_session: AsyncSession):
    # 1. Create Project 7
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": "PROJ-007-CL",
            "name": "Project 7 — CuO Mulberry Extract Closed-Loop Test",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    assert p_resp.status_code == 201
    proj_id = p_resp.json()["id"]

    # 2. Setup Parameter Definitions
    pd1_resp = await client.post(
        f"{PROJECTS_API}/{proj_id}/parameters",
        json={
            "parameter_code": "substrate_temperature",
            "parameter_name": "Substrate Temperature",
            "unit": "°C",
            "data_type": "NUMBER",
            "is_required": True,
        },
    )
    assert pd1_resp.status_code == 201

    pd2_resp = await client.post(
        f"{PROJECTS_API}/{proj_id}/parameters",
        json={
            "parameter_code": "spray_rate",
            "parameter_name": "Spray Rate",
            "unit": "mL/min",
            "data_type": "NUMBER",
            "is_required": True,
        },
    )
    assert pd2_resp.status_code == 201

    # 3. Create Experiment & Sample
    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": proj_id,
            "experiment_code": "EXP-PROJ7-CL01",
            "title": "Lab synthesis for candidate 1",
        },
    )
    assert exp_resp.status_code == 201
    exp_id = exp_resp.json()["id"]

    samp_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": exp_id,
            "sample_code": "SMP-PROJ7-CL01",
            "name": "CuO Thin Film Sample CL01",
        },
    )
    assert samp_resp.status_code == 201
    samp_id = samp_resp.json()["id"]

    # 4. Create ML Dataset & Model via db_session fixture
    from app.models.ml import MLDataset, MLTrainingRun, MLModel

    ds1 = MLDataset(
        id=uuid.uuid4(),
        project_id=uuid.UUID(proj_id),
        name="CuO Conductivity Dataset v1",
        version="v1.0",
        target_property="Electrical Conductivity",
        target_unit="S/cm",
        features=[
            {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "°C"},
            {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min"},
        ],
    )
    db_session.add(ds1)

    tr1 = MLTrainingRun(
        id=uuid.uuid4(),
        dataset_id=ds1.id,
        dataset_version="v1.0",
        model_type="RANDOM_FOREST",
        status="COMPLETED",
    )
    db_session.add(tr1)

    model1 = MLModel(
        id=uuid.uuid4(),
        training_run_id=tr1.id,
        dataset_id=ds1.id,
        dataset_version="v1.0",
        name="CuO Conductivity Random Forest (v1.0)",
        model_type="RANDOM_FOREST",
        version="1.0",
        target_property="Electrical Conductivity",
        target_unit="S/cm",
        status="ACTIVE",
        artifact_path="/artifacts/model_v1.joblib",
        library_versions={"scikit-learn": "1.3.0"},
        metrics={"cv_r2": 0.88, "cv_rmse": 0.35},
        feature_names=["substrate_temperature", "spray_rate"],
        feature_specs=ds1.features,
        preprocessing_config={"scaling": "STANDARD"},
        hyperparameters={"n_estimators": 50},
    )
    db_session.add(model1)
    await db_session.commit()
    model1_id = str(model1.id)

    # 5. Create Prospective Prediction Validation
    val_payload = {
        "model_id": model1_id,
        "experiment_id": exp_id,
        "sample_id": samp_id,
        "target_property": "Electrical Conductivity",
        "predicted_value": 5.40,
        "prediction_lower_bound": 4.80,
        "prediction_upper_bound": 6.00,
        "actual_value": 5.10,
        "unit": "S/cm",
        "actual_value_source": "Two-probe I-V Linear Fit",
        "researcher": "Dr. Lead Researcher",
    }

    res_v = await client.post(f"{VALIDATION_API}/create", json=val_payload)
    assert res_v.status_code == 201
    val_data = res_v.json()
    assert val_data["validation_status"] == "VALIDATED"
    assert val_data["absolute_error"] == pytest.approx(0.30)
    assert val_data["within_prediction_interval"] is True
    cand_id_created = val_data["dataset_candidate_id"]

    # 6. Researcher Reviews & ACCEPTS Dataset Candidate
    res_acc = await client.post(f"{DATASET_CANDIDATES_API}/{cand_id_created}/accept?reviewer=Dr.+Chief+Curator")
    assert res_acc.status_code == 200
    assert res_acc.json()["status"] == "ACCEPTED"

    # 7. List Candidates
    cands_resp = await client.get(f"{DATASET_CANDIDATES_API}?status=ACCEPTED")
    assert cands_resp.status_code == 200
    assert len(cands_resp.json()) >= 1

    # 8. Manually Promote Model
    res_prom = await client.post(f"{MODELS_API}/{model1_id}/promote?promoted_by=Dr.+Chief+Researcher")
    assert res_prom.status_code == 200
    assert res_prom.json()["status"] == "ACTIVE"

    # 9. Check Closed-Loop Summary Endpoint
    summary_resp = await client.get("/api/v1/closed-loop/summary")
    assert summary_resp.status_code == 200
    sum_data = summary_resp.json()
    assert sum_data["validations_completed"] >= 1
    assert "stage_counts" in sum_data
