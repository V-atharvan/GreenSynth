"""
GreenSynth Analytics — Machine Learning REST API Router

Provides endpoints for ML dataset management, dataset validation, model training & cross-validation,
model registry lifecycle (approval/rejection), and prediction generation.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.ml.schemas import (
    MLDatasetCreateInput,
    MLDatasetRecordResponse,
    MLDatasetResponse,
    MLModelApprovalInput,
    MLModelResponse,
    MLPredictInput,
    MLPredictionResponse,
    MLTrainingRunCreateInput,
    MLTrainingRunResponse,
)
from app.ml.services.dataset_service import MLDatasetService
from app.ml.services.prediction_service import MLPredictionService
from app.ml.services.registry_service import MLRegistryService
from app.ml.services.training_service import MLTrainingService

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# ── DATASET ENDPOINTS ─────────────────────────────────────────

@router.post(
    "/datasets",
    response_model=MLDatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ML dataset and extract eligible observations",
)
async def create_dataset(
    payload: MLDatasetCreateInput,
    db: AsyncSession = Depends(get_db),
) -> MLDatasetResponse:
    """Creates a versioned ML dataset definition, validates target leakage, and extracts eligible observations."""
    service = MLDatasetService(db)
    try:
        dataset, _quality = await service.create_dataset(payload)
        return MLDatasetResponse.model_validate(dataset)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/datasets",
    response_model=list[MLDatasetResponse],
    summary="List ML datasets for a project",
)
async def list_datasets(
    project_id: uuid.UUID = Query(..., description="Project ID filter"),
    db: AsyncSession = Depends(get_db),
) -> list[MLDatasetResponse]:
    """List versioned ML datasets created for a project."""
    service = MLDatasetService(db)
    datasets = await service.list_datasets(project_id)
    return [MLDatasetResponse.model_validate(d) for d in datasets]


@router.get(
    "/datasets/{dataset_id}",
    response_model=MLDatasetResponse,
    summary="Get ML dataset details",
)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MLDatasetResponse:
    """Fetch dataset metadata by ID."""
    service = MLDatasetService(db)
    try:
        ds = await service.get_dataset(dataset_id)
        return MLDatasetResponse.model_validate(ds)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/datasets/{dataset_id}/records",
    response_model=list[MLDatasetRecordResponse],
    summary="List dataset records with eligibility and provenance",
)
async def list_dataset_records(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MLDatasetRecordResponse]:
    """List observation rows in a dataset showing eligibility status and exclusion reasons."""
    service = MLDatasetService(db)
    recs = await service.list_dataset_records(dataset_id)
    return [MLDatasetRecordResponse.model_validate(r) for r in recs]


# ── TRAINING ENDPOINTS ────────────────────────────────────────

@router.post(
    "/training-runs",
    response_model=list[MLModelResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Train candidate ML models on a dataset",
)
async def train_models(
    payload: MLTrainingRunCreateInput,
    db: AsyncSession = Depends(get_db),
) -> list[MLModelResponse]:
    """Executes preprocessing, cross-validation, and model training for candidate algorithms on an ML dataset."""
    service = MLTrainingService(db)
    try:
        models = await service.run_training(payload)
        return [MLModelResponse.model_validate(m) for m in models]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/training-runs/{run_id}",
    response_model=MLTrainingRunResponse,
    summary="Get training run execution details",
)
async def get_training_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MLTrainingRunResponse:
    """Fetch training run execution metrics and parameters by ID."""
    service = MLTrainingService(db)
    try:
        tr = await service.get_training_run(run_id)
        return MLTrainingRunResponse.model_validate(tr)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/training-runs",
    response_model=list[MLTrainingRunResponse],
    summary="List training runs for a dataset",
)
async def list_training_runs(
    dataset_id: uuid.UUID = Query(..., description="Dataset ID filter"),
    db: AsyncSession = Depends(get_db),
) -> list[MLTrainingRunResponse]:
    """List training execution runs for a dataset."""
    service = MLTrainingService(db)
    runs = await service.list_training_runs(dataset_id)
    return [MLTrainingRunResponse.model_validate(r) for r in runs]


# ── MODEL REGISTRY ENDPOINTS ──────────────────────────────────

@router.get(
    "/models",
    response_model=list[MLModelResponse],
    summary="List registered ML models",
)
async def list_models(
    dataset_id: uuid.UUID | None = Query(default=None, description="Optional dataset filter"),
    status_filter: str | None = Query(default=None, alias="status", description="Optional status filter"),
    db: AsyncSession = Depends(get_db),
) -> list[MLModelResponse]:
    """List registered machine learning models."""
    service = MLRegistryService(db)
    models = await service.list_models(dataset_id=dataset_id, status=status_filter)
    return [MLModelResponse.model_validate(m) for m in models]


@router.get(
    "/models/{model_id}",
    response_model=MLModelResponse,
    summary="Get registered model details",
)
async def get_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MLModelResponse:
    """Fetch registered model details, metrics, and feature importances."""
    service = MLRegistryService(db)
    try:
        model = await service.get_model(model_id)
        return MLModelResponse.model_validate(model)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/models/{model_id}/approve",
    response_model=MLModelResponse,
    summary="Researcher approves model for production candidate use",
)
async def approve_model(
    model_id: uuid.UUID,
    payload: MLModelApprovalInput | None = None,
    db: AsyncSession = Depends(get_db),
) -> MLModelResponse:
    """Transitions model status to PRODUCTION_CANDIDATE after explicit researcher review."""
    service = MLRegistryService(db)
    try:
        notes = payload.notes if payload else None
        model = await service.approve_model(model_id, notes=notes)
        return MLModelResponse.model_validate(model)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/models/{model_id}/reject",
    response_model=MLModelResponse,
    summary="Reject model definition",
)
async def reject_model(
    model_id: uuid.UUID,
    payload: MLModelApprovalInput | None = None,
    db: AsyncSession = Depends(get_db),
) -> MLModelResponse:
    """Transitions model status to REJECTED."""
    service = MLRegistryService(db)
    try:
        notes = payload.notes if payload else None
        model = await service.reject_model(model_id, notes=notes)
        return MLModelResponse.model_validate(model)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ── PREDICTION ENDPOINTS ──────────────────────────────────────

@router.post(
    "/models/{model_id}/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate prediction using a registered model",
)
async def generate_prediction(
    model_id: uuid.UUID,
    payload: MLPredictInput,
    db: AsyncSession = Depends(get_db),
) -> MLPredictionResponse:
    """Generates continuous property prediction with uncertainty bounds and applicability domain check."""
    service = MLPredictionService(db)
    try:
        pred = await service.predict(model_id, payload)
        return MLPredictionResponse.model_validate(pred)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/predictions",
    response_model=list[MLPredictionResponse],
    summary="List generated predictions",
)
async def list_predictions(
    model_id: uuid.UUID | None = Query(default=None, description="Optional model ID filter"),
    db: AsyncSession = Depends(get_db),
) -> list[MLPredictionResponse]:
    """List historical prediction records with applicability status and uncertainty bounds."""
    service = MLPredictionService(db)
    preds = await service.list_predictions(model_id)
    return [MLPredictionResponse.model_validate(p) for p in preds]


@router.post(
    "/predictions/{prediction_id}/validate",
    summary="Link prediction to actual laboratory measurement and compute validation error",
)
async def validate_prediction(
    prediction_id: uuid.UUID,
    actual_value: float = Query(..., description="Actual measured laboratory value"),
    actual_target_property: str | None = Query(default=None, description="Actual target property name"),
    actual_unit: str | None = Query(default=None, description="Actual unit"),
    experiment_id: uuid.UUID | None = Query(default=None),
    sample_id: uuid.UUID | None = Query(default=None),
    validated_by: str = Query(default="Dr. Chief Researcher"),
    source_type: str = Query(default="MEASURED_PROPERTY"),
    actual_synthesis_params: str | None = Query(default=None, description="JSON string of actual synthesis params"),
    db: AsyncSession = Depends(get_db),
):
    """Link prediction to actual experiment result, enforce target and unit gates, compute errors and condition deviations."""
    import json
    from app.ml.validation.validation_service import ValidationService
    val_service = ValidationService(db)
    syn_params = None
    if actual_synthesis_params:
        try:
            syn_params = json.loads(actual_synthesis_params)
        except Exception:
            syn_params = None

    try:
        val_rec = await val_service.validate_prediction_against_actual(
            prediction_id=prediction_id,
            actual_value=actual_value,
            actual_target_property=actual_target_property,
            actual_unit=actual_unit,
            experiment_id=experiment_id,
            sample_id=sample_id,
            validated_by=validated_by,
            source_type=source_type,
            actual_synthesis_params=syn_params,
        )
        return {
            "validation_id": str(val_rec.id),
            "prediction_id": str(val_rec.prediction_id),
            "predicted_value": val_rec.predicted_value,
            "actual_value": val_rec.actual_value,
            "error": val_rec.error,
            "absolute_error": val_rec.absolute_error,
            "relative_error": val_rec.relative_error,
            "percentage_error": val_rec.percentage_error,
            "actual_inside_interval": val_rec.actual_inside_interval,
            "validation_status": val_rec.validation_status,
            "quality_status": val_rec.quality_status,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/models/{model_id}/performance",
    summary="Get model performance snapshot and metrics",
)
async def get_model_performance(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Evaluate and return current model performance snapshot."""
    from app.ml.validation.model_monitoring_service import ModelMonitoringService
    mon_service = ModelMonitoringService(db)
    try:
        snapshot = await mon_service.evaluate_model_performance(model_id)
        return {
            "snapshot_id": str(snapshot.id),
            "model_id": str(snapshot.model_id),
            "model_version": snapshot.model_version,
            "validation_count": snapshot.validation_count,
            "mae": snapshot.mae,
            "rmse": snapshot.rmse,
            "r2": snapshot.r2,
            "mean_error": snapshot.mean_error,
            "median_absolute_error": snapshot.median_absolute_error,
            "interval_coverage": snapshot.interval_coverage,
            "performance_status": snapshot.performance_status,
            "evaluation_date": snapshot.evaluation_date.isoformat() if snapshot.evaluation_date else None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/models/{model_id}/health",
    summary="Get model health status and indicators",
)
async def get_model_health(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch model health summary including validation count, MAE drift, and review recommendations."""
    from app.ml.validation.model_monitoring_service import ModelMonitoringService
    mon_service = ModelMonitoringService(db)
    try:
        snapshot = await mon_service.evaluate_model_performance(model_id)
        recommendation = "Model is stable and suitable for predictions."
        if snapshot.performance_status in ("WARNING", "DEGRADED", "CRITICAL"):
            recommendation = "Model review recommended due to observed performance deterioration relative to training baseline."

        return {
            "model_id": str(model_id),
            "status": snapshot.performance_status,
            "validation_count": snapshot.validation_count,
            "mae": snapshot.mae,
            "rmse": snapshot.rmse,
            "bias": "Positive (Underprediction)" if snapshot.mean_error > 0.05 else ("Negative (Overprediction)" if snapshot.mean_error < -0.05 else "Unbiased"),
            "recommendation": recommendation,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/models/{model_id}/review",
    summary="Submit researcher review for a model",
)
async def submit_model_review(
    model_id: uuid.UUID,
    review_status: str = Query(..., description="REVIEWED, REQUIRES_INVESTIGATION, ACCEPTED, REJECTED, RETIRED"),
    reviewer: str = Query(default="Dr. Chief Researcher"),
    notes: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Log researcher review or status change for a model."""
    from app.models.ml_validation import ModelReview
    rev = ModelReview(
        id=uuid.uuid4(),
        model_id=model_id,
        review_status=review_status,
        reviewer=reviewer,
        notes=notes,
    )
    db.add(rev)
    await db.commit()
    return {"review_id": str(rev.id), "model_id": str(model_id), "status": review_status, "reviewer": reviewer}


@router.post(
    "/models/{model_id}/retire",
    summary="Retire model from generating future predictions",
)
async def retire_model(
    model_id: uuid.UUID,
    reviewer: str = Query(default="Dr. Chief Researcher"),
    notes: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Transitions model status to RETIRED."""
    from app.ml.services.registry_service import MLRegistryService
    reg_service = MLRegistryService(db)
    try:
        model = await reg_service.reject_model(model_id, notes=f"RETIRED by {reviewer}: {notes or ''}")
        model.status = "RETIRED"
        await db.commit()
        return {"model_id": str(model_id), "status": "RETIRED"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/reports/{model_id}",
    summary="Export Markdown ML Model Report",
)
async def generate_model_report(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Export comprehensive Markdown ML Model Report."""
    from app.ml.services.registry_service import MLRegistryService
    from fastapi.responses import Response
    reg_service = MLRegistryService(db)
    try:
        model = await reg_service.get_model(model_id)
        md_content = f"""# Machine Learning Model Report

## 1. Model Identification
- **Model Name:** {model.name}
- **Model ID:** {model.id}
- **Model Type:** {model.model_type}
- **Version:** {model.version}
- **Status:** {model.status}
- **SHA256 Checksum:** {model.artifact_hash or 'N/A'}

## 2. Dataset & Target Specification
- **Dataset Version:** {model.dataset_version}
- **Target Property:** {model.target_property} ({model.target_unit})
- **Features:** {', '.join(model.feature_names)}
- **Random Seed:** {model.random_seed}

## 3. Evaluation Metrics
- **Train MAE:** {model.metrics.get('train_mae')} | **Train R²:** {model.metrics.get('train_r2')}
- **CV MAE:** {model.metrics.get('cv_mae')} | **CV R²:** {model.metrics.get('cv_r2')}
- **Overfitting Warning:** {model.metrics.get('overfitting_warning')}

## 4. Feature Importance (Model-Derived)
{model.feature_importance}

## 5. Disclaimers & Scope Boundaries
- Feature importance represents model-derived predictive association, NOT physical causation.
- Model predictions are labeled `PREDICTED` and must be validated by real laboratory experiments.
"""
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=ml_model_{model_id}_report.md"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
