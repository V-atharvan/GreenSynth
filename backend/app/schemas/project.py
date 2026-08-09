"""
GreenSynth Analytics — Project Pydantic Schemas

Request validation and response serialisation for the /api/v1/projects endpoints.
SQLAlchemy models are never exposed directly through the API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ProjectStatus


# ── Base ───────────────────────────────────────────────────

class ProjectBase(BaseModel):
    """Fields shared by create and update schemas."""

    name: str = Field(..., min_length=1, max_length=512, description="Full project name")
    project_code: str = Field(
        ..., min_length=1, max_length=32, description="Short unique code, e.g. P7"
    )
    description: str | None = Field(default=None, max_length=2000)
    material: str = Field(..., min_length=1, max_length=128, description="e.g. CuO")
    extract: str = Field(..., min_length=1, max_length=128, description="e.g. Mulberry")
    solvent: str = Field(..., min_length=1, max_length=128, description="e.g. Ethanol")
    synthesis_method: str = Field(
        ..., min_length=1, max_length=128, description="e.g. Spray Pyrolysis"
    )


# ── Create ─────────────────────────────────────────────────

class ProjectCreate(ProjectBase):
    """Schema for POST /api/v1/projects."""

    status: ProjectStatus = ProjectStatus.ACTIVE


# ── Update ─────────────────────────────────────────────────

class ProjectUpdate(BaseModel):
    """Schema for PUT /api/v1/projects/{id}. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=2000)
    material: str | None = Field(default=None, min_length=1, max_length=128)
    extract: str | None = Field(default=None, min_length=1, max_length=128)
    solvent: str | None = Field(default=None, min_length=1, max_length=128)
    synthesis_method: str | None = Field(default=None, min_length=1, max_length=128)
    status: ProjectStatus | None = None


# ── Response ───────────────────────────────────────────────

class ProjectResponse(ProjectBase):
    """Schema for project API responses."""

    id: UUID
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """Lightweight project summary used in lists and relationships."""

    id: UUID
    project_code: str
    name: str
    material: str
    synthesis_method: str
    status: ProjectStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
