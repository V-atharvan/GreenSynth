"""
GreenSynth Analytics — SEM Pydantic Schemas

Input and response schemas for SEM image metadata, scale calibration, annotations, and manual distance measurements.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SEMMetadataUpdate(BaseModel):
    magnification: float | None = Field(default=None, gt=0.0)
    accelerating_voltage_kv: float | None = Field(default=None, gt=0.0)
    working_distance_mm: float | None = Field(default=None, gt=0.0)
    detector: str | None = Field(default=None, max_length=64)
    scale_bar_nm: float | None = Field(default=None, gt=0.0)
    scale_bar_pixels: float | None = Field(default=None, gt=0.0)
    notes: str | None = Field(default=None, max_length=1000)


class SEMMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_file_id: UUID
    magnification: float | None = None
    accelerating_voltage_kv: float | None = None
    working_distance_mm: float | None = None
    detector: str | None = None
    scale_bar_nm: float | None = None
    scale_bar_pixels: float | None = None
    nm_per_pixel: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SEMAnnotationCreate(BaseModel):
    annotation_type: str = Field(default="point", description="point, line, rectangle, note")
    coordinates_json: dict = Field(..., description="x, y, width, height, x2, y2 coordinates")
    label: str = Field(..., max_length=128)
    notes: str | None = Field(default=None, max_length=1000)


class SEMAnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_file_id: UUID
    annotation_type: str
    coordinates_json: dict
    label: str
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime


class SEMMeasurementCreate(BaseModel):
    pixel_distance: float = Field(..., gt=0.0, description="Measured distance in screen pixels")
    label: str | None = Field(default="Particle Size", max_length=128)


class SEMMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_file_id: UUID
    pixel_distance: float
    physical_distance_nm: float | None = None
    unit: str
    label: str | None = None
    calibration_info: dict | None = None
    created_by: str | None = None
    created_at: datetime
