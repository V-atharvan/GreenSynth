"""
GreenSynth Analytics — Machine Learning Pydantic Schemas

Defines request/response payload schemas for datasets, model training runs,
model registry, and prediction generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── DATASET SCHEMAS ──────────────────────────────────────────

class MLDatasetFeatureSpec(BaseModel):
    feature_name: str = Field(..., description="Unique feature identifier name")
    source_parameter: str = Field(..., description="Parameter code or calculated property name")
    unit: str = Field(..., description="Measurement unit")
    data_type: str = Field(default="NUMBER", description="NUMBER, TEXT, ENUM")


class MLDatasetCreateInput(BaseModel):
    project_id: uuid.UUID = Field(..., description="Target parent project ID")
    name: str = Field(..., min_length=2, max_length=128, description="Dataset name")
    description: str | None = None
    target_property: str = Field(..., description="Target property name (e.g. Conductivity)")
    target_type: str = Field(default="MEASURED", description="MEASURED or CALCULATED")
    target_unit: str = Field(..., description="Target unit (e.g. S/cm)")
    features: list[MLDatasetFeatureSpec] = Field(..., min_items=1, description="Selected feature definitions")
    filters: dict[str, Any] | None = None
    experiment_ids: list[uuid.UUID] | None = None


class MLDatasetRecordResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    analysis_run_id: uuid.UUID | None = None
    feature_values: dict[str, Any]
    target_value: float | None = None
    target_unit: str | None = None
    is_eligible: bool
    exclusion_reason: str | None = None
    provenance_details: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class MLDatasetResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    version: str
    description: str | None = None
    target_property: str
    target_type: str
    target_unit: str
    features: list[dict[str, Any]]
    filters: dict[str, Any] | None = None
    preprocessing_config: dict[str, Any] | None = None
    status: str
    is_synthetic: bool
    eligible_count: int
    excluded_count: int
    exclusion_summary: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── TRAINING SCHEMAS ─────────────────────────────────────────

class MLTrainingRunCreateInput(BaseModel):
    dataset_id: uuid.UUID = Field(..., description="Target dataset ID")
    model_types: list[str] = Field(
        default=["MEAN_BASELINE", "LINEAR_REGRESSION", "RIDGE", "RANDOM_FOREST", "GRADIENT_BOOSTING"],
        description="List of model types to train and compare",
    )
    scaling: str = Field(default="STANDARD", description="STANDARD or NONE")
    cv_folds: int = Field(default=5, ge=2, le=20, description="Cross-validation folds")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")
    hyperparameters: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Optional hyperparameter overrides per model type"
    )


class MLTrainingRunResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version: str
    model_type: str
    preprocessing_version: str
    hyperparameters: dict[str, Any] | None = None
    random_seed: int
    cv_folds: int
    training_metrics: dict[str, Any] | None = None
    validation_metrics: dict[str, Any] | None = None
    test_metrics: dict[str, Any] | None = None
    overfitting_warning: bool
    low_data_warning: bool
    status: str
    started_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


# ── MODEL REGISTRY SCHEMAS ────────────────────────────────────

class MLModelApprovalInput(BaseModel):
    notes: str | None = Field(default=None, description="Researcher approval justification")


class MLModelResponse(BaseModel):
    id: uuid.UUID
    training_run_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version: str
    name: str
    model_type: str
    version: str
    target_property: str
    target_type: str
    target_unit: str
    feature_names: list[str]
    feature_specs: list[dict[str, Any]]
    preprocessing_config: dict[str, Any]
    hyperparameters: dict[str, Any]
    metrics: dict[str, Any]
    feature_importance: dict[str, float] | None = None
    library_versions: dict[str, str]
    status: str
    approval_notes: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── PREDICTION SCHEMAS ────────────────────────────────────────

class MLPredictInput(BaseModel):
    input_parameters: dict[str, float] = Field(
        ..., description="Map of feature names to continuous numerical values"
    )
    notes: str | None = None


class MLPredictionResponse(BaseModel):
    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_id: uuid.UUID
    input_parameters: dict[str, float]
    predicted_property: str
    predicted_value: float
    unit: str
    uncertainty_lower: float | None = None
    uncertainty_upper: float | None = None
    uncertainty_method: str | None = None
    applicability_status: str
    applicability_details: dict[str, Any] | None = None
    warnings: list[str] | None = None
    created_at: datetime

    class Config:
        from_attributes = True
