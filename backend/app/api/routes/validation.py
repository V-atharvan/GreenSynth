"""
GreenSynth Analytics — Validation REST API Router

Endpoints for Validation Criteria, Level 2 Holdout Prediction Validation, Level 3 Prospective Experimental Validation,
Validation Reports, Model Performance History, and Model Retraining Workflows with full authorization.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_authorized_project_ids,
    get_current_project,
    get_current_user,
    get_db,
    verify_project_access,
)
from app.ml.schemas import MLModelResponse
from app.ml.validation.criterion_service import CriterionService
from app.ml.validation.schemas import (
    HoldoutValidationCreateInput,
    HoldoutValidationResponse,
    ModelPerformanceHistoryResponse,
    ModelRetrainInput,
    ProspectiveExperimentCreateInput,
    ProspectiveExperimentResponse,
    ValidationCriterionCreateInput,
    ValidationCriterionResponse,
    ValidationResultResponse,
)
from app.ml.validation.validation_service import ValidationService
from app.models.analysis import CalculatedProperty
from app.models.experiment import Experiment
from app.models.ml import MLDataset, MLModel, MLPrediction
from app.models.project import Project
from app.models.user import User
from app.models.validation import DatasetCandidate, ProspectiveExperiment, ValidationResult

router = APIRouter(tags=["Model & Experimental Validation"])


# ── CRITERIA ENDPOINTS ────────────────────────────────────────

@router.post(
    "/validation/criteria",
    response_model=ValidationCriterionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create researcher-defined validation criterion",
)
async def create_criterion(
    payload: ValidationCriterionCreateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidationCriterionResponse:
    """Creates a researcher-defined threshold criterion for prediction validation."""
    if getattr(payload, "project_id", None) is not None and not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(payload.project_id, current_project, current_user)

    service = CriterionService(db)
    try:
        crit = await service.create_criterion(payload)
        return ValidationCriterionResponse.model_validate(crit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/validation/criteria",
    response_model=list[ValidationCriterionResponse],
    summary="List validation criteria",
)
async def list_criteria(
    property_name: str | None = Query(default=None, description="Optional target property filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ValidationCriterionResponse]:
    """List validation criteria."""
    service = CriterionService(db)
    criteria = await service.list_criteria(property_name)
    return [ValidationCriterionResponse.model_validate(c) for c in criteria]


# ── HOLDOUT VALIDATION ENDPOINTS ──────────────────────────────

@router.post(
    "/validation/holdout",
    response_model=HoldoutValidationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Level 2 holdout prediction validation",
)
async def execute_holdout_validation(
    payload: HoldoutValidationCreateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HoldoutValidationResponse:
    """Validates model prediction against an experiment deliberately excluded from training. Enforces zero data leakage."""
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == payload.model_id)
    )
    row_m = res_m.first()
    if not row_m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    res_e = await db.execute(
        select(Experiment).where(Experiment.id == payload.experiment_id)
    )
    exp = res_e.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")

    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if row_m[1] not in auth_ids or exp.project_id not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model or Experiment not found.")

    service = ValidationService(db)
    try:
        record = await service.execute_holdout_validation(payload)
        return HoldoutValidationResponse.model_validate(record)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ── PROSPECTIVE EXPERIMENT ENDPOINTS ──────────────────────────

@router.post(
    "/validation/prospective",
    response_model=ProspectiveExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Approve prediction for prospective physical lab experiment",
)
async def create_prospective_experiment(
    payload: ProspectiveExperimentCreateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProspectiveExperimentResponse:
    """Creates a prospective experiment tracking record after researcher explicitly approves a model prediction."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(payload.project_id, current_project, current_user)

    service = ValidationService(db)
    try:
        prosp = await service.create_prospective_experiment(payload)
        return ProspectiveExperimentResponse.model_validate(prosp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/validation/prospective/{prospective_id}/link-result",
    response_model=ValidationResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link laboratory experiment & characterization result to prospective prediction",
)
async def link_prospective_result(
    prospective_id: uuid.UUID,
    laboratory_experiment_id: uuid.UUID = Query(..., description="Completed lab experiment ID"),
    sample_id: uuid.UUID = Query(..., description="Characterized sample ID"),
    criterion_id: uuid.UUID | None = Query(default=None, description="Optional validation criterion ID"),
    measurement_uncertainty: float | None = Query(default=None, description="Optional lab measurement uncertainty"),
    notes: str | None = Query(default=None, description="Optional researcher notes"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidationResultResponse:
    """Links physical laboratory characterization result to prospective prediction and evaluates validation criterion."""
    res_p = await db.execute(
        select(ProspectiveExperiment).where(ProspectiveExperiment.id == prospective_id)
    )
    p_exp = res_p.scalar_one_or_none()
    if not p_exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospective experiment not found.")

    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_exp.project_id not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospective experiment not found.")

    service = ValidationService(db)
    try:
        vr = await service.link_prospective_result(
            prospective_id=prospective_id,
            laboratory_experiment_id=laboratory_experiment_id,
            sample_id=sample_id,
            criterion_id=criterion_id,
            measurement_uncertainty=measurement_uncertainty,
            notes=notes,
        )
        return ValidationResultResponse.model_validate(vr)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ── VALIDATION RESULTS & REPORTS ──────────────────────────────

@router.get(
    "/validation/results",
    response_model=list[ValidationResultResponse],
    summary="List validation results",
)
async def list_validation_results(
    model_id: uuid.UUID | None = Query(default=None, description="Optional model ID filter"),
    project_id: uuid.UUID | None = Query(default=None, description="Optional project ID filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ValidationResultResponse]:
    """List validation comparison results for authorized project scope."""
    stmt = (
        select(ValidationResult)
        .join(Experiment, ValidationResult.experiment_id == Experiment.id)
        .order_by(ValidationResult.created_at.desc())
    )

    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        stmt = stmt.where(Experiment.project_id == current_project.id)
    elif project_id is not None:
        stmt = stmt.where(Experiment.project_id == project_id)

    if model_id is not None:
        stmt = stmt.where(ValidationResult.model_id == model_id)

    res = await db.execute(stmt)
    results = res.scalars().all()
    return [ValidationResultResponse.model_validate(r) for r in results]


# ── MODEL PERFORMANCE HISTORY & RETRAINING ───────────────────

@router.get(
    "/models/{model_id}/performance-history",
    response_model=ModelPerformanceHistoryResponse,
    summary="Get model performance history (statistical vs physical experimental)",
)
async def get_performance_history(
    model_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelPerformanceHistoryResponse:
    """Fetches model performance history with IDOR protection."""
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == model_id)
    )
    row_m = res_m.first()
    if not row_m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if row_m[1] not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    service = ValidationService(db)
    try:
        history = await service.get_performance_history(model_id)
        return ModelPerformanceHistoryResponse(
            model_id=uuid.UUID(history.model_id),
            model_name=history.model_name,
            model_version=history.model_version,
            target_property=history.target_property,
            statistical_metrics=history.statistical_metrics,
            n_experimental_validations=history.n_experimental_validations,
            experimental_mae=history.experimental_mae,
            experimental_rmse=history.experimental_rmse,
            interval_coverage_rate=history.interval_coverage_rate,
            small_sample_warning=history.small_sample_warning,
            warnings=history.warnings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/models/{model_id}/retrain",
    response_model=list[MLModelResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Retrain model incorporating new validation data (creates Dataset v2 & Model v2)",
)
async def retrain_model(
    model_id: uuid.UUID,
    payload: ModelRetrainInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MLModelResponse]:
    """Requests model retraining with IDOR protection."""
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == model_id)
    )
    row_m = res_m.first()
    if not row_m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if row_m[1] not in auth_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    service = ValidationService(db)
    try:
        new_models = await service.retrain_model(model_id, payload, created_by=current_user.full_name or "Researcher")
        return [MLModelResponse.model_validate(m) for m in new_models]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ── PHASE 13 CLOSED-LOOP LEARNING & DATASET CANDIDATE ENDPOINTS ────────

@router.get(
    "/validation/pending",
    summary="Get pending recommendation-driven experiments queue ready for prediction vs actual validation",
)
async def get_pending_validation_queue(
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves pending prospective experiments for authorized project that have completed physical characterizations ready for validation."""
    stmt = select(ProspectiveExperiment)

    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        if project_id is not None:
            verify_project_access(uuid.UUID(project_id), current_project, current_user)
        stmt = stmt.where(ProspectiveExperiment.project_id == current_project.id)
    elif project_id is not None:
        stmt = stmt.where(ProspectiveExperiment.project_id == uuid.UUID(project_id))

    res_p = await db.execute(stmt)
    prospective_list = res_p.scalars().all()
    queue_items = []

    for p_exp in prospective_list:
        existing_val = None
        if p_exp.laboratory_experiment_id:
            res_v = await db.execute(
                select(ValidationResult).where(ValidationResult.experiment_id == p_exp.laboratory_experiment_id)
            )
            existing_val = res_v.scalar_one_or_none()

        if existing_val:
            continue

        calc_prop = None
        if p_exp.sample_id:
            res_cp = await db.execute(
                select(CalculatedProperty).where(CalculatedProperty.sample_id == p_exp.sample_id)
            )
            calc_prop = res_cp.scalar_one_or_none()

        queue_items.append({
            "prospective_id": str(p_exp.id),
            "model_id": str(p_exp.model_id),
            "model_version": p_exp.model_version,
            "prediction_id": str(p_exp.prediction_id),
            "project_id": str(p_exp.project_id),
            "approval_status": p_exp.approval_status,
            "laboratory_experiment_id": str(p_exp.laboratory_experiment_id) if p_exp.laboratory_experiment_id else None,
            "sample_id": str(p_exp.sample_id) if p_exp.sample_id else None,
            "has_calculated_property": calc_prop is not None,
            "calculated_property": calc_prop.property_name if calc_prop else None,
            "calculated_value": calc_prop.value if calc_prop else None,
            "calculated_unit": calc_prop.unit if calc_prop else None,
            "created_at": p_exp.created_at.isoformat() if p_exp.created_at else None,
        })

    return queue_items


@router.post(
    "/validation/create",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Prediction vs Actual laboratory validation result",
)
async def create_validation_result(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validates predicted value against actual lab characterization result with IDOR verification."""
    from app.validation.prediction_comparator import PredictionComparator

    model_id = uuid.UUID(payload["model_id"])
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == model_id)
    )
    row_m = res_m.first()
    if not row_m:
        raise HTTPException(status_code=404, detail=f"MLModel {model_id} not found.")

    exp_id = uuid.UUID(payload["experiment_id"])
    res_e = await db.execute(
        select(Experiment).where(Experiment.id == exp_id)
    )
    exp = res_e.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if row_m[1] not in auth_ids or exp.project_id not in auth_ids:
            raise HTTPException(status_code=404, detail="Model or Experiment not found.")

    model = row_m[0]

    # Unit & Target verification
    conv_val, final_unit, conv_notes = PredictionComparator.validate_target_and_units(
        predicted_target=model.target_property,
        actual_target=payload.get("target_property", model.target_property),
        predicted_unit=payload.get("unit", "S/cm"),
        actual_unit=payload.get("unit", "S/cm"),
        actual_value=float(payload["actual_value"]),
    )

    abs_err, signed_err, rel_err = PredictionComparator.calculate_errors(
        predicted=float(payload["predicted_value"]),
        actual=conv_val,
    )

    within_interval = PredictionComparator.check_prediction_interval(
        actual=conv_val,
        lower_bound=payload.get("prediction_lower_bound"),
        upper_bound=payload.get("prediction_upper_bound"),
    )

    val_status = "VALIDATED"
    if rel_err is not None and rel_err > 0.50:
        val_status = "FAILED"

    vr = ValidationResult(
        id=uuid.uuid4(),
        recommendation_id=uuid.UUID(payload["recommendation_id"]) if payload.get("recommendation_id") else None,
        candidate_id=uuid.UUID(payload["candidate_id"]) if payload.get("candidate_id") else None,
        experiment_id=exp_id,
        sample_id=uuid.UUID(payload["sample_id"]),
        model_id=model_id,
        model_version=model.version,
        dataset_version=getattr(model, "dataset_version", "v1.0"),
        target_property=model.target_property,
        predicted_value=float(payload["predicted_value"]),
        prediction_lower_bound=payload.get("prediction_lower_bound"),
        prediction_upper_bound=payload.get("prediction_upper_bound"),
        actual_value=conv_val,
        actual_value_source=payload.get("actual_value_source", "Calculated from laboratory characterization"),
        actual_measurement_uncertainty=payload.get("actual_measurement_uncertainty"),
        unit=final_unit,
        error=signed_err,
        signed_error=signed_err,
        absolute_error=abs_err,
        relative_error=rel_err,
        is_within_prediction_interval=within_interval,
        validation_type=payload.get("validation_type", "PROSPECTIVE"),
        validation_status=val_status,
        validation_method=payload.get("validation_method", "Direct Characterization Comparison"),
        evidence_level="MODERATE",
        researcher=payload.get("researcher", current_user.full_name or "Dr. Validation Engineer"),
        notes=payload.get("notes", conv_notes),
    )
    db.add(vr)
    await db.flush()

    # Propose DatasetCandidate for future retraining
    cand = DatasetCandidate(
        id=uuid.uuid4(),
        candidate_dataset_id=f"candidate_{str(vr.id)[:8]}",
        experiment_id=vr.experiment_id,
        sample_id=vr.sample_id,
        validation_id=vr.id,
        proposed_target=model.target_property,
        data_quality_status="VALID",
        researcher_review_status="PENDING_REVIEW",
        notes=f"Proposed automatically from validation {vr.id}",
    )
    db.add(cand)
    await db.commit()

    return {
        "id": str(vr.id),
        "validation_status": vr.validation_status,
        "absolute_error": vr.absolute_error,
        "signed_error": vr.signed_error,
        "relative_error": vr.relative_error,
        "within_prediction_interval": vr.is_within_prediction_interval,
        "dataset_candidate_id": str(cand.id),
        "evidence_level": vr.evidence_level,
    }


@router.post("/validation/results/{id}/confirm", summary="Confirm validation result after researcher verification")
async def confirm_validation_result(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirms a validation result with IDOR verification."""
    res_vr = await db.execute(
        select(ValidationResult, Experiment.project_id)
        .join(Experiment, ValidationResult.experiment_id == Experiment.id)
        .where(ValidationResult.id == id)
    )
    row = res_vr.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"ValidationResult {id} not found.")

    vr, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"ValidationResult {id} not found.")

    vr.validation_status = "VALIDATED"
    await db.commit()
    return {"id": str(vr.id), "status": "VALIDATED"}


@router.post("/validation/results/{id}/review", summary="Flag validation result for researcher review")
async def flag_validation_review(
    id: uuid.UUID,
    reason: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Flags a validation result for manual review with IDOR verification."""
    res_vr = await db.execute(
        select(ValidationResult, Experiment.project_id)
        .join(Experiment, ValidationResult.experiment_id == Experiment.id)
        .where(ValidationResult.id == id)
    )
    row = res_vr.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"ValidationResult {id} not found.")

    vr, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"ValidationResult {id} not found.")

    vr.validation_status = "REQUIRES_REVIEW"
    vr.notes = f"{vr.notes or ''} | Flagged for review: {reason}".strip()
    await db.commit()
    return {"id": str(vr.id), "status": "REQUIRES_REVIEW"}


@router.get("/dataset-candidates", summary="List dataset candidates for researcher review")
async def list_dataset_candidates(
    status: str | None = Query(default=None, description="PENDING_REVIEW, ACCEPTED, REJECTED"),
    project_id: uuid.UUID | None = Query(default=None, description="Optional project filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists candidate data points for authorized project scope proposed for future training datasets."""
    stmt = (
        select(DatasetCandidate)
        .join(Experiment, DatasetCandidate.experiment_id == Experiment.id)
    )

    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        stmt = stmt.where(Experiment.project_id == current_project.id)
    elif project_id is not None:
        stmt = stmt.where(Experiment.project_id == project_id)

    if status:
        stmt = stmt.where(DatasetCandidate.researcher_review_status == status)

    res_c = await db.execute(stmt)
    cands = res_c.scalars().all()

    return [
        {
            "id": str(c.id),
            "candidate_dataset_id": c.candidate_dataset_id,
            "experiment_id": str(c.experiment_id),
            "sample_id": str(c.sample_id),
            "validation_id": str(c.validation_id),
            "proposed_target": c.proposed_target,
            "data_quality_status": c.data_quality_status,
            "researcher_review_status": c.researcher_review_status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
            "reviewer": c.reviewer,
            "notes": c.notes,
        }
        for c in cands
    ]


@router.post("/dataset-candidates/{id}/accept", summary="Researcher accepts dataset candidate")
async def accept_dataset_candidate(
    id: uuid.UUID,
    reviewer: str = Query(default="Dr. Dataset Curator"),
    notes: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Researcher accepts a candidate into future dataset version with IDOR verification."""
    res_c = await db.execute(
        select(DatasetCandidate, Experiment.project_id)
        .join(Experiment, DatasetCandidate.experiment_id == Experiment.id)
        .where(DatasetCandidate.id == id)
    )
    row = res_c.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"DatasetCandidate {id} not found.")

    cand, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"DatasetCandidate {id} not found.")

    cand.researcher_review_status = "ACCEPTED"
    cand.reviewer = reviewer
    if notes:
        cand.notes = f"{cand.notes or ''} | Review: {notes}".strip()

    await db.commit()
    return {"id": str(cand.id), "status": cand.researcher_review_status}


@router.post("/dataset-candidates/{id}/reject", summary="Researcher rejects dataset candidate")
async def reject_dataset_candidate(
    id: uuid.UUID,
    reviewer: str = Query(default="Dr. Dataset Curator"),
    notes: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Researcher rejects a dataset candidate with IDOR verification."""
    res_c = await db.execute(
        select(DatasetCandidate, Experiment.project_id)
        .join(Experiment, DatasetCandidate.experiment_id == Experiment.id)
        .where(DatasetCandidate.id == id)
    )
    row = res_c.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"DatasetCandidate {id} not found.")

    cand, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"DatasetCandidate {id} not found.")

    cand.researcher_review_status = "REJECTED"
    cand.reviewer = reviewer
    if notes:
        cand.notes = f"{cand.notes or ''} | Review: {notes}".strip()

    await db.commit()
    return {"id": str(cand.id), "status": cand.researcher_review_status}


@router.post("/models/{id}/promote", summary="Researcher manually promotes a model to ACTIVE state")
async def promote_model(
    id: uuid.UUID,
    promoted_by: str = Query(default="Dr. Chief Researcher"),
    notes: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually promotes a model to ACTIVE status with IDOR verification."""
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == id)
    )
    row = res_m.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"MLModel {id} not found.")

    target_model, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"MLModel {id} not found.")

    res_act = await db.execute(
        select(MLModel)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(
            MLModel.target_property == target_model.target_property,
            MLModel.status == "ACTIVE",
            MLModel.id != id,
            MLDataset.project_id == p_id,
        )
    )
    for old_model in res_act.scalars().all():
        old_model.status = "RETIRED"

    target_model.status = "ACTIVE"
    target_model.approved_by = promoted_by
    await db.commit()
    return {"id": str(target_model.id), "name": target_model.name, "version": target_model.version, "status": target_model.status}


@router.post("/models/{id}/retire", summary="Retire a model version")
async def retire_model(
    id: uuid.UUID,
    retired_by: str = Query(default="Dr. Chief Researcher"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retires a model version with IDOR verification."""
    res_m = await db.execute(
        select(MLModel, MLDataset.project_id)
        .join(MLDataset, MLModel.dataset_id == MLDataset.id)
        .where(MLModel.id == id)
    )
    row = res_m.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"MLModel {id} not found.")

    target_model, p_id = row
    if not current_user.is_admin:
        auth_ids = await get_authorized_project_ids(current_user, db)
        if p_id not in auth_ids:
            raise HTTPException(status_code=404, detail=f"MLModel {id} not found.")

    target_model.status = "RETIRED"
    await db.commit()
    return {"id": str(target_model.id), "name": target_model.name, "status": target_model.status}


@router.get("/closed-loop/summary", summary="Get Research Loop visual workflow metrics & stage counts")
async def get_closed_loop_summary(
    project_id: uuid.UUID | None = Query(default=None, description="Optional project filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves 10-stage Research Loop visual workflow counts and aggregate metrics for authorized project scope."""
    from app.validation.validation_quality import ValidationQuality

    target_proj_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_proj_id = current_project.id
    elif project_id is not None:
        target_proj_id = project_id

    # Count experiments
    q_exp = select(func.count(Experiment.id))
    if target_proj_id:
        q_exp = q_exp.where(Experiment.project_id == target_proj_id)
    res_exp = await db.execute(q_exp)
    exp_count = res_exp.scalar() or 0

    # Count recommendations
    from app.models.recommendation import Recommendation
    q_rec = select(func.count(Recommendation.id))
    if target_proj_id:
        q_rec = q_rec.where(Recommendation.project_id == target_proj_id)
    res_rec = await db.execute(q_rec)
    rec_count = res_rec.scalar() or 0

    # Validation results
    q_vals = select(ValidationResult).join(Experiment, ValidationResult.experiment_id == Experiment.id)
    if target_proj_id:
        q_vals = q_vals.where(Experiment.project_id == target_proj_id)
    res_vals_all = await db.execute(q_vals)
    vals = res_vals_all.scalars().all()
    val_count = len(vals)

    within_count = sum(1 for v in vals if v.is_within_prediction_interval is True)
    mae_vals = [v.absolute_error for v in vals if v.absolute_error is not None]
    avg_mae = float(sum(mae_vals) / len(mae_vals)) if mae_vals else None

    rel_vals = [v.relative_error for v in vals if v.relative_error is not None]
    avg_rel = float(sum(rel_vals) / len(rel_vals)) if rel_vals else None

    # Dataset candidates
    q_cand = select(func.count(DatasetCandidate.id)).join(Experiment, DatasetCandidate.experiment_id == Experiment.id)
    if target_proj_id:
        q_cand = q_cand.where(Experiment.project_id == target_proj_id)
    res_cand = await db.execute(q_cand)
    cand_count = res_cand.scalar() or 0

    # Active model and dataset
    q_am = select(MLModel).join(MLDataset, MLModel.dataset_id == MLDataset.id).where(MLModel.status == "ACTIVE")
    if target_proj_id:
        q_am = q_am.where(MLDataset.project_id == target_proj_id)
    res_am = await db.execute(q_am.limit(1))
    active_model = res_am.scalar_one_or_none()

    q_ad = select(MLDataset).order_by(MLDataset.created_at.desc())
    if target_proj_id:
        q_ad = q_ad.where(MLDataset.project_id == target_proj_id)
    res_ad = await db.execute(q_ad.limit(1))
    active_dataset = res_ad.scalar_one_or_none()

    n_samples = len(vals)
    evidence = ValidationQuality.evaluate_evidence_level(n_samples, avg_rel)

    return {
        "total_experiments": exp_count,
        "total_recommendations": rec_count,
        "recommendations_tested": val_count,
        "validations_completed": val_count,
        "predictions_within_interval": within_count,
        "supported_recommendations": sum(1 for v in vals if v.validation_status == "VALIDATED"),
        "partially_supported_recommendations": 0,
        "not_supported_recommendations": sum(1 for v in vals if v.validation_status == "FAILED"),
        "inconclusive_recommendations": sum(1 for v in vals if v.validation_status == "REQUIRES_REVIEW"),
        "avg_absolute_error": avg_mae,
        "avg_relative_error": avg_rel,
        "sample_count_n": n_samples,
        "evidence_level": evidence,
        "active_model_version": active_model.version if active_model else "v1.0",
        "active_dataset_version": getattr(active_dataset, "dataset_version", "v1.0") if active_dataset else "v1.0",
        "stage_counts": {
            "experimental_data": exp_count,
            "dataset": getattr(active_dataset, "total_records", 0) if active_dataset else 0,
            "model": active_model.version if active_model else "v1.0",
            "recommendation": rec_count,
            "experiment": exp_count,
            "actual_result": val_count,
            "validation": val_count,
            "dataset_candidate": cand_count,
            "new_dataset": getattr(active_dataset, "dataset_version", "v1.0") if active_dataset else "v1.0",
            "new_model": active_model.version if active_model else "v1.0",
        },
    }
