"""
GreenSynth Analytics — UV-Vis Pydantic Schemas

Input payload & response schemas for UV-Vis spectrum processing, Tauc plot transformations,
and optical band gap calculation.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.scientific.uvvis.transforms import TransitionType


class UVVisPreprocessingConfig(BaseModel):
    baseline_subtraction: bool = Field(default=False, description="Baseline subtraction")
    smoothing: bool = Field(default=True, description="Savitzky-Golay smoothing")
    savgol_window: int = Field(default=11, ge=3, le=101)
    savgol_polyorder: int = Field(default=3, ge=1, le=5)


class TaucConfig(BaseModel):
    transition_type: TransitionType = Field(
        default=TransitionType.DIRECT_ALLOWED,
        description="DIRECT_ALLOWED (n=2) or INDIRECT_ALLOWED (n=0.5)",
    )
    sample_thickness_cm: float | None = Field(
        default=None, gt=0.0, description="Optional sample thickness in cm"
    )
    fit_energy_min_ev: float | None = Field(default=None, description="Fitting region start in eV")
    fit_energy_max_ev: float | None = Field(default=None, description="Fitting region end in eV")


class UVVisAnalysisInput(BaseModel):
    preprocessing: UVVisPreprocessingConfig = Field(default_factory=UVVisPreprocessingConfig)
    tauc: TaucConfig = Field(default_factory=TaucConfig)
    notes: str | None = Field(default=None, max_length=1000)


class TaucDataPoint(BaseModel):
    wavelength_nm: float
    absorbance: float
    photon_energy_ev: float
    tauc_y: float


class TaucFitLinePoint(BaseModel):
    photon_energy_ev: float
    fit_y: float


class TaucProcessedResponse(BaseModel):
    analysis_run_id: UUID
    transition_type: str
    using_alpha: bool
    thickness_cm: float | None
    warning_msg: str | None
    data_points: list[TaucDataPoint]
    fit_line: list[TaucFitLinePoint] = Field(default_factory=list)
    band_gap_ev: float | None = None
    r_squared: float | None = None
    total_points: int
