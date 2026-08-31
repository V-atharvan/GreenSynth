"""
GreenSynth Analytics — Administrator Schemas

Defines response structures for Administrator overview, system audits,
and global resource listings.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdminOverviewResponse(BaseModel):
    """System-wide summary metrics for Platform Administrators."""

    model_config = ConfigDict(from_attributes=True)

    total_projects: int = Field(default=0, description="Total active synthesis projects (P1–P8)")
    total_groups: int = Field(default=0, description="Total registered research groups")
    total_students: int = Field(default=0, description="Total registered student / researcher accounts")
    total_experiments: int = Field(default=0, description="Total experimental runs across all projects")
    total_samples: int = Field(default=0, description="Total synthesized samples across all projects")
    total_characterizations: int = Field(default=0, description="Total characterization datasets uploaded")
    total_ml_models: int = Field(default=0, description="Total trained ML models across all projects")
    total_recommendations: int = Field(default=0, description="Total recommendation studio sessions")
    total_optimization_runs: int = Field(default=0, description="Total multi-objective optimization runs")
