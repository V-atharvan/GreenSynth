"""
GreenSynth Analytics — Phase 17 Closed-Loop Prediction Validation Integration Test
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment, ExperimentStatus
from app.models.ml import MLDataset, MLModel, MLPrediction, MLTrainingRun
from app.models.project import Project, ProjectStatus
from app.models.sample import Sample


@pytest.mark.asyncio
async def test_phase17_closed_loop_pipeline(client: AsyncClient, db_session: AsyncSession):
    """End-to-end integration test for Phase 17 Closed-Loop Validation & Model Health Monitoring."""

    # 1. Create Project 7, MLDataset, MLModel, and MLPrediction
    proj = Project(
        id=uuid.uuid4(),
        project_code=f"PROJ-007-V17-{uuid.uuid4().hex[:4]}",
        name="Project 7 - Phase 17 Validation",
        description="CuO Spray Pyrolysis prediction validation test",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(proj)
    await db_session.commit()

    ds = MLDataset(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="DS-P17-001",
        version="v1.0",
        target_property="conductivity_s_cm",
        target_type="MEASURED",
        target_unit="S/cm",
        features=[{"feature_name": "substrate_temperature", "unit": "°C"}],
        status="IMMUTABLE",
        eligible_count=5,
    )
    db_session.add(ds)
    await db_session.commit()

    tr = MLTrainingRun(
        id=uuid.uuid4(),
        dataset_id=ds.id,
        dataset_version="v1.0",
        model_type="RANDOM_FOREST",
        preprocessing_version="v1",
        status="COMPLETED",
    )
    db_session.add(tr)
    await db_session.commit()

    model = MLModel(
        id=uuid.uuid4(),
        training_run_id=tr.id,
        dataset_id=ds.id,
        dataset_version="v1.0",
        name="CuO RF Model V1",
        model_type="RANDOM_FOREST",
        version="1.0",
        target_property="conductivity_s_cm",
        target_type="MEASURED",
        target_unit="S/cm",
        feature_names=["substrate_temperature"],
        feature_specs=[{"feature_name": "substrate_temperature", "unit": "°C"}],
        preprocessing_config={"scaling": "STANDARD"},
        hyperparameters={"n_estimators": 10},
        artifact_path="data/models/test/model.joblib",
        metrics={"cv_mae": 0.25, "cv_r2": 0.85},
        library_versions={"scikit-learn": "1.3.0"},
        status="PRODUCTION_CANDIDATE",
    )
    db_session.add(model)
    await db_session.commit()

    pred = MLPrediction(
        id=uuid.uuid4(),
        model_id=model.id,
        model_version="1.0",
        dataset_id=ds.id,
        input_parameters={"substrate_temperature": 350.0},
        predicted_property="conductivity_s_cm",
        predicted_value=5.2,
        unit="S/cm",
        uncertainty_lower=4.5,
        uncertainty_upper=5.9,
        applicability_status="VALID",
    )
    db_session.add(pred)
    await db_session.commit()

    exp = Experiment(
        id=uuid.uuid4(),
        project_id=proj.id,
        experiment_code=f"EXP-V17-{uuid.uuid4().hex[:4]}",
        title="Validation Experiment 1",
        status=ExperimentStatus.COMPLETED,
    )
    db_session.add(exp)
    await db_session.commit()

    # 2. Target Mismatch Rejection Test
    res_mismatch = await client.post(
        f"/api/v1/ml/predictions/{pred.id}/validate?actual_value=1.5&actual_target_property=band_gap"
    )
    assert res_mismatch.status_code == 400
    assert "Target mismatch" in res_mismatch.json()["detail"]

    # 3. Successful Validation with Condition Deviation & Unit Match
    syn_params_json = '{"substrate_temperature": 347.0}'
    res_val = await client.post(
        f"/api/v1/ml/predictions/{pred.id}/validate?actual_value=4.7&actual_target_property=conductivity_s_cm&actual_unit=S/cm&experiment_id={exp.id}&actual_synthesis_params={syn_params_json}"
    )
    assert res_val.status_code == 200
    val_data = res_val.json()

    assert val_data["validation_status"] == "VALIDATED"
    assert val_data["predicted_value"] == 5.2
    assert val_data["actual_value"] == 4.7
    assert val_data["error"] == -0.5
    assert val_data["absolute_error"] == 0.5
    assert val_data["actual_inside_interval"] is True

    # 4. Check Model Performance & Health API
    res_perf = await client.get(f"/api/v1/ml/models/{model.id}/performance")
    assert res_perf.status_code == 200
    perf_data = res_perf.json()
    assert perf_data["validation_count"] >= 1

    res_health = await client.get(f"/api/v1/ml/models/{model.id}/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert "status" in health_data

    # 5. Researcher Model Review & Retirement
    res_rev = await client.post(f"/api/v1/ml/models/{model.id}/review?review_status=ACCEPTED&notes=Validated successfully.")
    assert res_rev.status_code == 200

    res_ret = await client.post(f"/api/v1/ml/models/{model.id}/retire?notes=Superseded by newer dataset.")
    assert res_ret.status_code == 200
    assert res_ret.json()["status"] == "RETIRED"
