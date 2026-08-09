"""
GreenSynth Analytics — Optimization Objectives Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ObjectiveConstraint(BaseModel):
    parameter: str
    operator: str = Field(..., description=">=, <=, =, BETWEEN, IN")
    value: float | str | list[float | str]
    unit: str | None = None


class ObjectiveCreateInput(BaseModel):
    project_id: UUID
    name: str = Field(..., max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    target_property: str = Field(..., max_length=128, description="Target material property e.g. Electrical Conductivity")
    direction: str = Field(..., description="MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE")
    target_value: float | None = Field(default=None)
    min_value: float | None = Field(default=None)
    max_value: float | None = Field(default=None)
    unit: str | None = Field(default=None, max_length=64)
    weight: float = Field(default=1.0, gt=0.0)
    synthesis_method: str | None = Field(default=None, max_length=128)
    solvent: str | None = Field(default=None, max_length=128)
    constraints: list[ObjectiveConstraint] | None = Field(default=None)


class ObjectiveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    version: str
    description: str | None = None
    target_property: str
    direction: str
    target_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = None
    weight: float
    synthesis_method: str | None = None
    solvent: str | None = None
    constraints: list[dict] | None = None
    status: str
    created_by: str | None = None
    created_at: datetime
