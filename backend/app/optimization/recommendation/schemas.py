"""
GreenSynth Analytics — Recommendation Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── CANDIDATE SCHEMAS ─────────────────────────────────────────

class CandidateModifyInput(BaseModel):
    modified_parameter_set: dict[str, Any] = Field(..., description="Researcher modified parameter values")
    modification_reason: str = Field(..., description="Researcher rationale for modifying proposed condition")


class RecommendationCandidateResponse(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    rank: int
    parameter_set: dict[str, Any]
    predicted_properties: dict[str, Any]
    uncertainty: dict[str, Any]
    applicability_status: str
    evidence_level: str
    evidence_score: float
    objective_score: float
    constraint_status: str
    novelty_score: float
    overall_score: float
    explanation: str
    warning: str | None = None
    status: str
    modified_parameter_set: dict[str, Any] | None = None
    modification_reason: str | None = None
    created_experiment_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


# ── RECOMMENDATION SESSION SCHEMAS ────────────────────────────

class RecommendationGenerateInput(BaseModel):
    project_id: uuid.UUID = Field(..., description="Project ID (e.g. Project 7 CuO Mulberry)")
    objective_id: uuid.UUID = Field(..., description="Optimization Objective ID")
    model_id: uuid.UUID = Field(..., description="Validated ML Model ID")
    candidate_count: int = Field(default=5, ge=1, le=20, description="Top-N candidates to return")
    ranking_method: str = Field(default="BALANCED", description="BALANCED, EXPLOITATION, EXPLORATION")
    random_seed: int | None = Field(default=42, description="Random seed for candidate generation reproducibility")
    max_uncertainty_width: float | None = Field(default=None, description="Max acceptable prediction interval width filter")
    notes: str | None = None


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    objective_id: uuid.UUID
    model_id: uuid.UUID
    model_version: str
    dataset_id: uuid.UUID
    generated_at: datetime
    researcher: str | None = None
    status: str
    candidate_count: int
    ranking_method: str
    random_seed: int | None = None
    notes: str | None = None
    candidates: list[RecommendationCandidateResponse] = []

    class Config:
        from_attributes = True
