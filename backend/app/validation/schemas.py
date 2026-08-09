"""
GreenSynth Analytics — Closed-Loop Validation Pydantic Schemas
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class ValidationCreateInput(BaseModel):
    recommendation_id: Optional[uuid.UUID] = None
    candidate_id: Optional[uuid.UUID] = None
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    model_id: uuid.UUID
    prediction_id: Optional[uuid.UUID] = None
    
    target_property: str
    predicted_value: float
    prediction_lower_bound: Optional[float] = None
    prediction_upper_bound: Optional[float] = None
    
    actual_value: float
    actual_value_source: Optional[str] = "Calculated from laboratory characterization"
    actual_measurement_uncertainty: Optional[float] = None
    unit: str
    
    researcher: Optional[str] = "Dr. Validation Engineer"
    notes: Optional[str] = None


class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recommendation_id: Optional[uuid.UUID] = None
    candidate_id: Optional[uuid.UUID] = None
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_version: Optional[str] = None

    target_property: str
    predicted_value: float
    prediction_lower_bound: Optional[float] = None
    prediction_upper_bound: Optional[float] = None

    actual_value: float
    actual_value_source: Optional[str] = None
    actual_measurement_uncertainty: Optional[float] = None
    unit: str

    error: float
    signed_error: Optional[float] = None
    absolute_error: float
    relative_error: Optional[float] = None
    is_within_prediction_interval: Optional[bool] = None

    criterion_result: Optional[str] = None
    validation_type: str
    validation_status: str
    validation_method: Optional[str] = None
    evidence_level: Optional[str] = "MODERATE"
    is_synthetic: bool = False

    researcher: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime


class DatasetCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_dataset_id: str
    experiment_id: uuid.UUID
    sample_id: uuid.UUID
    validation_id: uuid.UUID
    proposed_target: str
    data_quality_status: str
    researcher_review_status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = None


class DatasetCandidateReviewInput(BaseModel):
    action: str  # ACCEPT, REJECT, FLAGGED_FOR_REVIEW
    reviewer: str = "Dr. Dataset Curator"
    notes: Optional[str] = None


class ModelPerformanceSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_version: str
    evaluation_type: str
    target_property: str
    sample_count: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    mean_error: Optional[float] = None
    created_at: datetime


class ParameterDeviationResponse(BaseModel):
    parameter_name: str
    recommended_value: Optional[float] = None
    planned_value: Optional[float] = None
    actual_value: Optional[float] = None
    absolute_deviation: Optional[float] = None
    percentage_deviation: Optional[float] = None
    unit: Optional[str] = None
    has_deviation: bool = False


class ResearchLoopMetricsResponse(BaseModel):
    total_experiments: int
    total_recommendations: int
    recommendations_tested: int
    validations_completed: int
    predictions_within_interval: int
    supported_recommendations: int
    partially_supported_recommendations: int
    not_supported_recommendations: int
    inconclusive_recommendations: int
    avg_absolute_error: Optional[float] = None
    avg_relative_error: Optional[float] = None
    sample_count_n: int
    evidence_level: str
    active_model_version: str
    active_dataset_version: str
