"""
GreenSynth Analytics — Design of Experiments (DOE) Pydantic Schemas (Phase 14 Extended)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FactorDefinition(BaseModel):
    parameter_code: str
    name: str
    factor_type: str = Field(default="CONTINUOUS", description="CONTINUOUS, CATEGORICAL, ORDINAL, DISCRETE")
    role: str = Field(default="CONTROLLABLE", description="CONTROLLABLE, BLOCK, COVARIATE")
    lower_bound: float | None = Field(default=None)
    upper_bound: float | None = Field(default=None)
    center_value: float | None = Field(default=None)
    unit: str | None = Field(default=None)
    levels: int | list[float | str] = Field(default=2, description="Number of levels for continuous, or array for discrete/categorical")


class ResponseDefinition(BaseModel):
    property_name: str
    unit: str | None = Field(default=None)
    direction: str = Field(default="MAXIMIZE", description="MAXIMIZE, MINIMIZE, TARGET, RANGE")
    target: float | None = Field(default=None)
    lower_limit: float | None = Field(default=None)
    upper_limit: float | None = Field(default=None)
    preferred_value: float | None = Field(default=None)
    weight: float = Field(default=1.0, ge=0.0)


class DOEConstraint(BaseModel):
    parameter_code: str
    operator: str = Field(..., description=">=, <=, =, BETWEEN, IN, CUSTOM_EXPRESSION")
    value: float | str | list[float | str]
    unit: str | None = None


class DOECreateInput(BaseModel):
    project_id: UUID
    objective_id: UUID | None = Field(default=None)
    name: str = Field(..., max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    research_question: str | None = Field(default=None)
    design_method: str = Field(
        ...,
        description="FULL_FACTORIAL, FRACTIONAL_FACTORIAL, CENTRAL_COMPOSITE, BOX_BEHNKEN, RANDOMIZED_CANDIDATE",
    )
    factors: list[FactorDefinition] = Field(..., min_items=1)
    responses: list[ResponseDefinition] | None = Field(default_factory=list)
    constraints: list[DOEConstraint] | None = Field(default=None)
    requested_runs: int = Field(default=10, gt=0)
    replicates: int = Field(default=1, ge=1)
    center_points: int = Field(default=0, ge=0)
    random_seed: int | None = Field(default=42)
    randomize_run_order: bool = Field(default=True)


class DOEWorkloadPreview(BaseModel):
    design_method: str
    factors_count: int
    base_runs: int
    replicates: int
    center_points: int
    total_runs: int
    design_resolution: str | None = None
    confounding_warning: str | None = None
    requires_workload_warning: bool = False
    warning_message: str | None = None


class DOEResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    objective_id: UUID | None = None
    name: str
    description: str | None = None
    research_question: str | None = None
    version: str
    design_method: str
    factors: list[dict]
    responses: list[dict] | None = None
    constraints: list[dict] | None = None
    requested_runs: int
    replicates: int
    center_points: int
    alpha_value: float | None = None
    design_resolution: str | None = None
    random_seed: int | None = None
    randomize_run_order: bool
    status: str
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ProposedExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doe_id: UUID
    design_condition_id: str
    design_order: int
    run_order: int
    replicate_number: int
    is_center_point: bool = False
    block: str | None = None
    factor_values: dict[str, float | str]
    measured_responses: dict[str, float] | None = None
    parameter_deviations: dict[str, dict] | None = None
    status: str = Field(..., description="PROPOSED, APPROVED, REJECTED, PLANNED, IN_PROGRESS, COMPLETED, FAILED, SKIPPED, CANCELLED")
    converted_experiment_id: UUID | None = None
    created_by: str | None = None
    created_at: datetime


class FactorCoverageItem(BaseModel):
    parameter_code: str
    name: str
    factor_type: str
    min_generated: float | str | None = None
    max_generated: float | str | None = None
    unique_levels: int


class DOEQualityReport(BaseModel):
    total_proposed_runs: int
    valid_runs: int
    invalid_runs: int
    intentional_replicates: int
    factor_coverage: list[FactorCoverageItem]
    warnings: list[str] = Field(default_factory=list)


class DOEAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doe_id: UUID
    doe_version: str
    response_property: str
    sample_count: int
    main_effects: dict[str, float]
    interaction_effects: dict[str, float] | None = None
    regression_model: dict | None = None
    fit_metrics: dict
    residual_diagnostics: dict | None = None
    created_at: datetime
