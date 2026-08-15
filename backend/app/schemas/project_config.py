"""
GreenSynth Analytics — Phase 19 Project Configuration & Matrix Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CatalogItemResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    status: str = "ACTIVE"

    class Config:
        from_attributes = True


class ProjectMatrixRow(BaseModel):
    project_code: str
    project_name: str
    material: str
    biomass: str | None = "—"
    extract: str
    solvent: str
    synthesis_method: str
    experiment_count: int = 0
    sample_count: int = 0
    characterization_count: int = 0
    dataset_status: str = "CONFIGURED"
    model_status: str = "NOT_TRAINED"
    optimization_status: str = "READY"


class ProjectConfigurationResponse(BaseModel):
    project_id: uuid.UUID
    project_code: str
    name: str
    material_system: str
    material: str
    biomass: str | None = None
    extract: str
    solvent: str
    synthesis_method: str
    method_code: str | None = None
    current_version: str
    characterization_capabilities: dict[str, bool]
    analysis_capabilities: dict[str, bool]
    optimization_capabilities: dict[str, bool]


class PropertyComparabilityRequest(BaseModel):
    source_project_code: str
    target_project_code: str
    source_property: str
    target_property: str


class PropertyComparabilityResponse(BaseModel):
    comparability_status: str = Field(..., description="COMPARABLE, COMPARABLE_WITH_WARNING, NOT_COMPARABLE")
    source_material: str
    target_material: str
    source_method: str
    target_method: str
    is_same_material_system: bool
    is_same_synthesis_method: bool
    is_same_solvent: bool
    reason: str
