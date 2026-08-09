"""
GreenSynth Analytics — XRD Pydantic Schemas

Input payload & response schemas for XRD pattern processing, peak detection,
and Scherrer crystallite size calculation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Analysis Input Parameters ───────────────────────────────

class PreprocessingConfig(BaseModel):
    baseline_subtraction: bool = Field(default=True, description="Subtract baseline")
    baseline_window: int = Field(default=50, ge=5, le=500, description="Rolling window size")
    smoothing: bool = Field(default=True, description="Apply Savitzky-Golay filter")
    savgol_window: int = Field(default=11, ge=3, le=101, description="Filter window length (odd)")
    savgol_polyorder: int = Field(default=3, ge=1, le=5, description="Polynomial order")


class PeakDetectionConfig(BaseModel):
    prominence: float | None = Field(default=None, ge=0.0, description="Minimum peak prominence")
    min_height: float | None = Field(default=None, ge=0.0, description="Minimum peak height")
    min_distance: int = Field(default=5, ge=1, le=100, description="Minimum index distance")


class ScherrerConfig(BaseModel):
    calculate_crystallite_size: bool = Field(default=True)
    wavelength_nm: float = Field(default=0.15406, gt=0.0, description="X-ray wavelength in nm (Cu-Ka = 0.15406)")
    shape_factor_k: float = Field(default=0.9, gt=0.0, description="Scherrer shape factor K")


class XRDAnalysisInput(BaseModel):
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    peak_detection: PeakDetectionConfig = Field(default_factory=PeakDetectionConfig)
    scherrer: ScherrerConfig = Field(default_factory=ScherrerConfig)
    notes: str | None = Field(default=None, max_length=1000)


# ── Response Schemas ────────────────────────────────────────

class XRDPeakResponse(BaseModel):
    id: UUID
    analysis_run_id: UUID
    peak_position: float = Field(..., description="2θ in degrees")
    intensity: float = Field(..., description="Intensity")
    fwhm: float | None = Field(default=None, description="FWHM in degrees")
    prominence: float | None = None
    width: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalculatedPropertyResponse(BaseModel):
    id: UUID
    sample_id: UUID
    analysis_run_id: UUID
    property_name: str
    value: float
    unit: str
    calculation_method: str
    formula: str | None
    assumptions: dict | None
    input_values: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class XRDDataPoint(BaseModel):
    two_theta: float
    raw_intensity: float
    processed_intensity: float | None = None


class XRDProcessedDataResponse(BaseModel):
    analysis_run_id: UUID
    data_points: list[XRDDataPoint]
    total_points: int


class XRDAnalysisRunResponse(BaseModel):
    id: UUID
    characterization_id: UUID
    input_file_id: UUID
    analysis_type: str
    status: str
    software_version: str
    parameters: dict | None
    assumptions: dict | None
    notes: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    peaks: list[XRDPeakResponse] = Field(default_factory=list)
    calculated_properties: list[CalculatedPropertyResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
