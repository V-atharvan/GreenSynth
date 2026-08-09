"""
GreenSynth Analytics — Phase 16 ML Prediction & Model Validation Integration Test
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentStatus
from app.models.ml import MLDataset, MLDatasetRecord
from app.models.project import Project, ProjectStatus
from app.models.sample import Sample


@pytest.mark.asyncio
async def test_ml_prediction_validation_pipeline(client: AsyncClient, db_session: AsyncSession):
    """End-to-end integration test for Phase 16 ML Prediction & Model Validation Workflow."""

    # 1. Create Project 7, Experiment, and Sample Data
    proj = Project(
        id=uuid.uuid4(),
        project_code=f"PROJ-007-ML-{uuid.uuid4().hex[:4]}",
        name="Project 7 - CuO Spray Pyrolysis ML Pipeline",
        description="ML synthesis prediction for CuO Mulberry thin films",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(proj)
    await db_session.commit()

    exp = Experiment(
        id=uuid.uuid4(),
        project_id=proj.id,
        experiment_code=f"EXP-ML-{uuid.uuid4().hex[:4]}",
        title="Spray Pyrolysis ML Training Set Exp",
        status=ExperimentStatus.COMPLETED,
    )
    db_session.add(exp)
    await db_session.commit()

    sample = Sample(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        sample_code=f"S-ML-{uuid.uuid4().hex[:4]}",
        name="CuO 350C 3mL",
    )
    db_session.add(sample)
    await db_session.commit()

    # 2. Create MLDataset
    ds = MLDataset(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="PROJECT7-ML-DATASET-001",
        version="v1.0",
        target_property="conductivity_s_cm",
        target_type="MEASURED",
        target_unit="S/cm",
        features=[
            {"feature_name": "substrate_temperature", "source_parameter": "substrate_temperature", "unit": "°C", "data_type": "NUMBER"},
            {"feature_name": "spray_rate", "source_parameter": "spray_rate", "unit": "mL/min", "data_type": "NUMBER"},
        ],
        status="ACTIVE",
        eligible_count=5,
    )
    db_session.add(ds)
    await db_session.commit()

    # Add 5 eligible records
    samples_data = [
        (300.0, 2.0, 1.2),
        (300.0, 5.0, 2.1),
        (350.0, 3.0, 3.4),
        (400.0, 2.0, 4.5),
        (400.0, 5.0, 5.8),
    ]
    for t_val, r_val, cond_val in samples_data:
        s_id = uuid.uuid4()
        s_rec = Sample(id=s_id, experiment_id=exp.id, sample_code=f"S-{uuid.uuid4().hex[:4]}", name="CuO")
        db_session.add(s_rec)
        await db_session.commit()

        rec = MLDatasetRecord(
            id=uuid.uuid4(),
            dataset_id=ds.id,
            experiment_id=exp.id,
            sample_id=s_id,
            feature_values={"substrate_temperature": t_val, "spray_rate": r_val},
            target_value=cond_val,
            target_unit="S/cm",
            is_eligible=True,
        )
        db_session.add(rec)
    await db_session.commit()

    # 3. Train Candidate ML Models via API
    train_payload = {
        "dataset_id": str(ds.id),
        "model_types": ["LINEAR_REGRESSION", "RIDGE", "LASSO", "RANDOM_FOREST", "GRADIENT_BOOSTING"],
        "scaling": "STANDARD",
        "cv_folds": 2,
        "random_seed": 42,
    }
    res_tr = await client.post("/api/v1/ml/training-runs", json=train_payload)
    assert res_tr.status_code == 201
    trained_models = res_tr.json()
    assert len(trained_models) == 5

    selected_model = trained_models[0]
    model_id = selected_model["id"]

    # 4. Approve Selected Model via API
    res_app = await client.post(f"/api/v1/ml/models/{model_id}/approve", json={"notes": "Approved for testing."})
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "PRODUCTION_CANDIDATE"

    # 5. Generate Prediction via API
    predict_payload = {
        "input_parameters": {"substrate_temperature": 375.0, "spray_rate": 3.5},
        "notes": "Candidate synthesis condition prediction",
    }
    res_pred = await client.post(f"/api/v1/ml/models/{model_id}/predict", json=predict_payload)
    assert res_pred.status_code == 201
    pred_data = res_pred.json()
    pred_id = pred_data["id"]
    assert pred_data["predicted_property"] == "conductivity_s_cm"
    assert pred_data["predicted_value"] > 0.0

    # 6. Validate Prediction against Actual Result via API
    res_val = await client.post(f"/api/v1/ml/predictions/{pred_id}/validate?actual_value=3.85&experiment_id={exp.id}")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["validation_status"] == "VALIDATED"
    assert val_data["actual_value"] == 3.85
    assert val_data["absolute_error"] >= 0.0
