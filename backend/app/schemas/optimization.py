"""
GreenSynth Analytics — Phase 18 Optimization Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Optimization Objective Schemas ──────────────────────

class OptimizationObjectiveBase(BaseModel):
    name: str = Field(..., max_length=128, description="Human-readable objective name")
    description: str | None = None
    target_property: str = Field(..., max_length=128, description="Target material property (e.g. conductivity_s_cm)")
    direction: str = Field(..., description="MAXIMIZE, MINIMIZE, TARGET")
    target_value: float | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    unit: str | None = None

    @field_validator("direction")
    def validate_direction(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("MAXIMIZE", "MINIMIZE", "TARGET"):
            raise ValueError("Direction must be MAXIMIZE, MINIMIZE, or TARGET")
        return v_upper


class OptimizationObjectiveCreate(OptimizationObjectiveBase):
    project_id: uuid.UUID
    created_by: str | None = "Researcher"


class OptimizationObjectiveResponse(OptimizationObjectiveBase):
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Optimization Constraint Schemas ─────────────────────

class OptimizationConstraintBase(BaseModel):
    constraint_type: str = Field(
        ...,
        description="PARAMETER_RANGE, PROPERTY_RANGE, FIXED_VALUE, CATEGORICAL_ALLOWED_VALUE, MODEL_DOMAIN",
    )
    target_code: str = Field(..., max_length=128)
    operator: str = Field(default="BETWEEN")
    minimum_value: float | None = None
    maximum_value: float | None = None
    fixed_value: float | None = None
    allowed_values: list[Any] | None = None
    unit: str | None = None
    is_hard_constraint: bool = True
    penalty_weight: float = 1.0


class OptimizationConstraintCreate(OptimizationConstraintBase):
    project_id: uuid.UUID


class OptimizationConstraintResponse(OptimizationConstraintBase):
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Search Space Schemas ─────────────────────────────────

class SearchSpaceValidationRequest(BaseModel):
    project_id: uuid.UUID
    parameters_override: dict[str, dict[str, Any]] | None = None
    constraints_override: list[dict[str, Any]] | None = None


class SearchSpaceValidationResponse(BaseModel):
    is_valid: bool
    warnings: list[str]
    errors: list[str]
    search_space: dict[str, Any]
    estimated_combinations: int | None = None


# ── Optimization Run Schemas ──────────────────────────────

class OptimizationRunCreate(BaseModel):
    project_id: uuid.UUID
    objective_id: uuid.UUID
    model_id: uuid.UUID
    generation_method: str = Field(default="RANDOM_SEARCH", description="GRID_SEARCH, RANDOM_SEARCH, MODEL_GUIDED_SEARCH")
    random_seed: int | None = 42
    requested_candidate_count: int = Field(default=10, ge=1, le=1000)
    allow_out_of_domain: bool = False
    notes: str | None = None
    created_by: str | None = "Researcher"


class OptimizationCandidateResponse(BaseModel):
    id: uuid.UUID
    optimization_run_id: uuid.UUID
    candidate_number: int
    rank: int
    parameter_values: dict[str, Any]
    parameter_units: dict[str, str]
    feasibility_status: str
    domain_status: str
    predictions: dict[str, Any]
    uncertainties: dict[str, Any]
    objective_score: float
    score_breakdown: dict[str, Any]
    evidence_score: float
    novelty_category: str
    parameter_distance: float
    nearby_experiment_ids: list[str]
    candidate_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OptimizationRunResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    objective_id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_id: uuid.UUID
    dataset_version: str
    generation_method: str
    random_seed: int | None
    requested_candidate_count: int
    feasible_candidate_count: int
    search_space_definition: dict[str, Any]
    constraints_definition: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    created_by: str | None = None
    notes: str | None = None
    candidates: list[OptimizationCandidateResponse] = []

    class Config:
        from_attributes = True


# ── Review & Selection Schemas ────────────────────────────

class CandidateReviewRequest(BaseModel):
    decision: str = Field(..., description="SELECTED, REJECTED, DEFERRED")
    reason: str | None = None
    notes: str | None = None
    reviewer_id: str = Field(default="Researcher")


class ProposedExperimentFromCandidateResponse(BaseModel):
    experiment_id: uuid.UUID
    experiment_code: str
    candidate_id: uuid.UUID
    status: str
    proposed_parameters: dict[str, Any]
    message: str


class OptimizationReportResponse(BaseModel):
    run_id: uuid.UUID
    project_code: str
    project_name: str
    objective_name: str
    target_property: str
    direction: str
    model_name: str
    model_version: str
    dataset_version: str
    model_health_status: str
    generation_method: str
    total_candidates_generated: int
    feasible_candidates_count: int
    top_candidates: list[OptimizationCandidateResponse]
    disclaimer: str
    generated_at: datetime
