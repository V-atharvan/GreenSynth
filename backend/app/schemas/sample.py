"""
GreenSynth Analytics — Sample Pydantic Schemas

Request validation and response serialisation for /api/v1/samples.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SampleStatus


# ── Base ───────────────────────────────────────────────────

class SampleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    material: str | None = Field(default=None, max_length=128)
    description: str | None = None
    notes: str | None = None


# ── Create ─────────────────────────────────────────────────

class SampleCreate(SampleBase):
    """Schema for POST /api/v1/samples."""

    experiment_id: UUID
    sample_code: str = Field(
        ..., min_length=1, max_length=64,
        description="Unique code, e.g. P7-EXP-001-S1"
    )
    status: SampleStatus = SampleStatus.PREPARED


# ── Update ─────────────────────────────────────────────────

class SampleUpdate(BaseModel):
    """Schema for PUT /api/v1/samples/{id}. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    material: str | None = Field(default=None, max_length=128)
    description: str | None = None
    notes: str | None = None
    status: SampleStatus | None = None


# ── Response ───────────────────────────────────────────────

class SampleResponse(SampleBase):
    """Full sample response."""

    id: UUID
    experiment_id: UUID
    sample_code: str
    status: SampleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SampleSummary(BaseModel):
    """Lightweight sample summary for lists."""

    id: UUID
    experiment_id: UUID
    sample_code: str
    name: str
    material: str | None
    status: SampleStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
