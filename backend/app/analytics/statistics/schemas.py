"""
GreenSynth Analytics — Analytics & Statistics Pydantic Schemas (Phase 15 Extended)

Input and response schemas for comparison dataset creation, dataset versioning,
descriptive statistics, Pearson/Spearman correlation matrices, linear/interaction/quadratic regression,
model diagnostics & Q-Q plots, evidence records, outlier flags, and data quality dashboards.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetCreateInput(BaseModel):
    project_id: UUID
    name: str = Field(..., max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    sample_ids: list[UUID] = Field(..., min_items=1)
    variables: list[str] = Field(..., min_items=1, description="Variable names e.g. substrate_temperature, band_gap_ev, conductivity_s_cm")
    filters: dict | None = Field(default=None)


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    version: str
    description: str | None = None
    sample_ids: list[UUID]
    variables: list[str]
    filters: dict | None = None
    created_by: str | None = None
    created_at: datetime


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    dataset_id: UUID | str
    project_id: UUID | str
    name: str
    version: str
    description: str | None = None
    included_sample_ids: list[UUID | str]
    included_experiment_ids: list[UUID | str]
    included_doe_run_ids: list[UUID | str] | None = None
    included_factors: list[str]
    included_responses: list[str]
    filtering_rules: dict | None = None
    exclusion_rules: dict | None = None
    summary_json: dict
    status: str
    created_by: str | None = None
    created_at: datetime


class ComparisonTableCell(BaseModel):
    variable: str
    value: float | str | None = None
    unit: str | None = None
    status: str = Field(..., description="MEASURED, CALCULATED, DETECTED")
    source: str | None = None


class ComparisonTableRow(BaseModel):
    sample_id: UUID | str
    sample_code: str
    sample_name: str
    experiment_code: str
    synthesis_method: str | None = None
    solvent: str | None = None
    cells: dict[str, ComparisonTableCell]


class DataQualityReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_samples: int
    variables_evaluated: list[str]
    missing_counts: dict[str, int]
    duplicate_count: int = 0
    outlier_count: int = 0
    unit_consistency: str = "PASS"
    quality_status: str = Field(default="PASS", description="PASS, WARNING, ERROR")
    warnings: list[str] = Field(default_factory=list)


DataQualityReport = DataQualityReportResponse


class ComparisonTableResponse(BaseModel):
    dataset_id: UUID | str
    dataset_name: str
    version: str
    total_samples: int
    variables: list[str]
    rows: list[ComparisonTableRow]
    quality_report: DataQualityReportResponse


class DescriptiveStatsItem(BaseModel):
    variable: str
    sample_size_n: int
    unit: str | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    variance: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    val_range: float | None = None
    q1: float | None = None
    q3: float | None = None
    iqr: float | None = None
    cv: float | None = None
    missing_count: int = 0


class CorrelationRequest(BaseModel):
    variables: list[str] = Field(..., min_items=2)
    method: str = Field(default="PEARSON", description="PEARSON, SPEARMAN")


class CorrelationResponse(BaseModel):
    x_variable: str
    y_variable: str
    method: str = "Pearson Correlation"
    pearson_r: float
    p_value: float | None = None
    sample_size_n: int
    interpretation: str
    warnings: list[str] = Field(default_factory=list)


class CorrelationMatrixResponse(BaseModel):
    method: str
    variables: list[str]
    matrix: dict[str, dict[str, float]]
    p_values: dict[str, dict[str, float]] | None = None
    sample_size_n: int
    warnings: list[str] = Field(default_factory=list)


class RegressionRequest(BaseModel):
    x_variables: list[str] = Field(..., min_items=1)
    y_variable: str
    model_type: str = Field(default="SIMPLE_LINEAR", description="SIMPLE_LINEAR, MULTIPLE_LINEAR, INTERACTION, QUADRATIC")
    include_interaction: bool = Field(default=False)
    include_quadratic: bool = Field(default=False)


class RegressionResponse(BaseModel):
    y_variable: str
    x_variables: list[str]
    model_type: str
    method: str = "Ordinary Least Squares"
    formula: str
    coefficients: dict[str, float]
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float
    adjusted_r_squared: float
    rmse: float
    mae: float
    aic: float | None = None
    bic: float | None = None
    confidence_interval: dict[str, list[float]] | None = None
    prediction_interval: dict[str, list[float]] | None = None
    sample_size_n: int
    interpretation: str
    warnings: list[str] = Field(default_factory=list)


class ModelDiagnosticsResponse(BaseModel):
    residuals: list[float]
    fitted_values: list[float]
    qq_sample_quantiles: list[float]
    qq_theoretical_quantiles: list[float]
    heteroscedasticity_warning: bool = False
    normality_warning: bool = False
    diagnostic_summary: str


class GroupStatsItem(BaseModel):
    group_value: str
    sample_size_n: int
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    min_val: float | None = None
    max_val: float | None = None


class GroupComparisonResponse(BaseModel):
    group_variable: str
    target_variable: str
    groups: list[GroupStatsItem]
    interpretation: str


class OutlierItem(BaseModel):
    sample_id: UUID | str
    sample_code: str
    variable: str
    value: float
    method: str
    score: float
    is_excluded: bool = False
    exclusion_reason: str | None = None


class OutlierReportResponse(BaseModel):
    variable: str
    method: str
    threshold: float
    total_inspected: int
    outliers_found: list[OutlierItem]


class EvidenceCreateInput(BaseModel):
    dataset_version_id: UUID | str
    statement: str = Field(..., max_length=1000)
    evidence_type: str = Field(..., description="OBSERVATION, ASSOCIATION, STATISTICAL_EFFECT, MODEL_ESTIMATE, VALIDATED_RESULT")
    variables: list[str] = Field(..., min_items=1)
    sample_size: int = Field(..., ge=1)
    statistical_method: str
    effect_estimate: float | None = None
    uncertainty: float | None = None
    confidence_interval: dict[str, float] | None = None
    prediction_interval: dict[str, float] | None = None
    limitations: list[str] | None = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    dataset_version_id: UUID | str
    analysis_run_id: UUID | str | None = None
    statement: str
    evidence_type: str
    variables: list[str]
    sample_size: int
    statistical_method: str
    effect_estimate: float | None = None
    uncertainty: float | None = None
    confidence_interval: dict[str, float] | None = None
    prediction_interval: dict[str, float] | None = None
    evidence_score: float
    scoring_criteria: dict
    limitations: list[str] | None = None
    status: str
    created_by: str | None = None
    created_at: datetime


class ReadinessGatesResponse(BaseModel):
    dataset_version_id: UUID | str
    is_ml_ready: bool
    ml_ready_criteria: dict[str, bool]
    is_optimization_ready: bool
    optimization_ready_criteria: dict[str, bool]
    disclaimer: str = "ML_READY / OPTIMIZATION_READY indicates compliance with software validation quality gates; it does not constitute peer-reviewed scientific proof."


class StatisticalAnalysisRunInput(BaseModel):
    analysis_type: str = Field(..., description="DESCRIPTIVE, CORRELATION, REGRESSION, GROUP_COMPARISON, OUTLIERS")
    x_variable: str | None = None
    y_variable: str | None = None
    group_variable: str | None = None


class StatisticalAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | str
    dataset_id: UUID | str
    analysis_run_id: UUID | str | None = None
    analysis_type: str
    x_variable: str | None = None
    y_variable: str | None = None
    group_variable: str | None = None
    method: str
    sample_size: int
    results_json: dict
    assumptions_json: dict | None = None
    warnings_json: dict | None = None
    created_by: str | None = None
    created_at: datetime
