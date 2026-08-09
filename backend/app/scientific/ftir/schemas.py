"""
GreenSynth Analytics — FTIR Pydantic Schemas

Input payload, peak response, annotation input, and response schemas for FTIR spectroscopy analysis.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FTIRPreprocessingConfig(BaseModel):
    smoothing: bool = Field(default=True)
    savgol_window: int = Field(default=11, ge=3)
    savgol_polyorder: int = Field(default=3, ge=1)


class FTIRPeakDetectionConfig(BaseModel):
    prominence: float | None = Field(default=None, ge=0.0)
    min_distance: int = Field(default=10, ge=1)


class FTIRAnalysisInput(BaseModel):
    preprocessing: FTIRPreprocessingConfig = Field(default_factory=FTIRPreprocessingConfig)
    peak_detection: FTIRPeakDetectionConfig = Field(default_factory=FTIRPeakDetectionConfig)
    notes: str | None = Field(default=None, max_length=1000)


class FTIRPeakItem(BaseModel):
    wavenumber_cm1: float
    signal_value: float
    prominence: float
    width_cm1: float


class FTIRDataPoint(BaseModel):
    wavenumber_cm1: float
    signal_value: float


class FTIRProcessedResponse(BaseModel):
    analysis_run_id: UUID
    signal_type: str
    data_points: list[FTIRDataPoint]
    detected_peaks: list[FTIRPeakItem]
    total_points: int


class FTIRAnnotationCreate(BaseModel):
    wavenumber_cm1: float = Field(..., description="Target peak wavenumber in cm^-1")
    label: str = Field(..., max_length=128, description="Short label e.g. C=O stretch")
    interpretation: str | None = Field(default=None, description="Researcher scientific interpretation")
    confidence: str | None = Field(default="Tentative", description="High, Medium, Tentative")
    notes: str | None = Field(default=None, max_length=1000)


class FTIRAnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    wavenumber_cm1: float
    label: str
    interpretation: str | None = None
    confidence: str | None = None
    created_by: str | None = None
    notes: str | None = None
    created_at: datetime
