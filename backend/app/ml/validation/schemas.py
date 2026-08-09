"""
GreenSynth Analytics — Validation Pydantic Schemas

Payload and response schemas for validation criteria, holdout validation,
prospective experiments, validation results, performance history, and retraining workflows.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── VALIDATION CRITERIA SCHEMAS ───────────────────────────────

class ValidationCriterionCreateInput(BaseModel):
    property_name: str = Field(..., description="Target property name (e.g. Electrical Conductivity)")
    metric: str = Field(..., description="ABSOLUTE_ERROR, RELATIVE_ERROR, WITHIN_INTERVAL")
    threshold: float = Field(..., description="Error threshold value")
    unit: str = Field(..., description="Measurement unit")
    comparison_operator: str = Field(default="<=", description="<=, >=, ==")
    description: str | None = None


class ValidationCriterionResponse(BaseModel):
    id: uuid.UUID
    property_name: str
    metric: str
    threshold: float
    unit: str
    comparison_operator: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── HOLDOUT VALIDATION SCHEMAS ────────────────────────────────

class HoldoutValidationCreateInput(BaseModel):
    model_id: uuid.UUID = Field(..., description="Model ID")
    experiment_id: uuid.UUID = Field(..., description="Holdout Experiment ID (must NOT be in training set)")
    sample_id: uuid.UUID = Field(..., description="Holdout Sample ID")
    criterion_id: uuid.UUID | None = None
    researcher: str | None = None
    notes: str | None = None


class HoldoutValidationResponse(BaseModel):
    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_id: uuid.UUID
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    target_property: str
    predicted_value: float
    actual_value: float
    unit: str
    error: float
    absolute_error: float
    relative_error: float | None = None
    status: str
    researcher: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── PROSPECTIVE EXPERIMENT SCHEMAS ─────────────────────────────

class ProspectiveExperimentCreateInput(BaseModel):
    prediction_id: uuid.UUID = Field(..., description="Model Prediction ID to validate")
    project_id: uuid.UUID = Field(..., description="Target Project ID")
    researcher: str | None = None
    notes: str | None = None


class ProspectiveExperimentResponse(BaseModel):
    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    prediction_id: uuid.UUID
    project_id: uuid.UUID
    proposed_conditions: dict[str, Any]
    researcher: str | None = None
    approval_status: str
    laboratory_experiment_id: uuid.UUID | None = None
    sample_id: uuid.UUID | None = None
    actual_result: float | None = None
    actual_unit: str | None = None
    measurement_uncertainty: float | None = None
    validation_status: str
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── VALIDATION RESULT SCHEMAS ─────────────────────────────────

class ValidationResultResponse(BaseModel):
    id: uuid.UUID
    prediction_id: uuid.UUID | None = None
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    target_property: str
    predicted_value: float
    prediction_lower_bound: float | None = None
    prediction_upper_bound: float | None = None
    actual_value: float
    actual_measurement_uncertainty: float | None = None
    unit: str
    error: float
    absolute_error: float
    relative_error: float | None = None
    is_within_prediction_interval: bool | None = None
    criterion_id: uuid.UUID | None = None
    criterion_result: str | None = None
    validation_type: str
    validation_status: str
    is_synthetic: bool
    researcher: str | None = None
    notes: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ── PERFORMANCE HISTORY & RETRAINING SCHEMAS ─────────────────

class ModelPerformanceHistoryResponse(BaseModel):
    model_id: uuid.UUID
    model_name: str
    model_version: str
    target_property: str
    statistical_metrics: dict[str, Any]
    n_experimental_validations: int
    experimental_mae: float | None = None
    experimental_rmse: float | None = None
    interval_coverage_rate: float | None = None
    small_sample_warning: bool
    warnings: list[str]


class ModelRetrainInput(BaseModel):
    notes: str | None = Field(default=None, description="Researcher justification for retraining dataset v2")
