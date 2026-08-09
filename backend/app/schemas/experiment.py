"""
GreenSynth Analytics — Experiment Pydantic Schemas

Request validation and response serialisation for /api/v1/experiments.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ExperimentStatus
from app.schemas.project import ProjectSummary


# ── Base ───────────────────────────────────────────────────

class ExperimentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    experiment_date: date | None = None
    researcher: str | None = Field(default=None, max_length=255)
    notes: str | None = None


# ── Create ─────────────────────────────────────────────────

class ExperimentCreate(ExperimentBase):
    """Schema for POST /api/v1/experiments."""

    project_id: UUID
    experiment_code: str = Field(
        ..., min_length=1, max_length=64,
        description="Unique code, e.g. P7-EXP-001"
    )
    status: ExperimentStatus = ExperimentStatus.PLANNED


# ── Update ─────────────────────────────────────────────────

class ExperimentUpdate(BaseModel):
    """Schema for PUT /api/v1/experiments/{id}. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=512)
    status: ExperimentStatus | None = None
    experiment_date: date | None = None
    researcher: str | None = Field(default=None, max_length=255)
    notes: str | None = None


# ── Response ───────────────────────────────────────────────

class ExperimentResponse(ExperimentBase):
    """Full experiment response."""

    id: UUID
    project_id: UUID
    experiment_code: str
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentWithProject(ExperimentResponse):
    """Experiment response that includes the parent project summary."""

    project: ProjectSummary


class ExperimentSummary(BaseModel):
    """Lightweight experiment summary for lists."""

    id: UUID
    project_id: UUID
    experiment_code: str
    title: str
    status: ExperimentStatus
    experiment_date: date | None
    researcher: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
