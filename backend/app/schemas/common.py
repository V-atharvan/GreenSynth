"""
GreenSynth Analytics — Common Pydantic Schemas

Shared types, enums, and response wrappers used across all API schemas.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Generic response wrapper ────────────────────────────────

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response envelope."""

    data: DataT
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated list response."""

    data: list[DataT]
    total: int
    page: int = 1
    page_size: int = 50


# ── Error responses ─────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response body returned by exception handlers."""

    error_code: str
    message: str
    field: str | None = None
    suggestion: str | None = None


# ── Status enums ────────────────────────────────────────────

class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ExperimentStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class SampleStatus(StrEnum):
    PREPARED = "PREPARED"
    READY_FOR_CHARACTERIZATION = "READY_FOR_CHARACTERIZATION"
    UNDER_ANALYSIS = "UNDER_ANALYSIS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


# ── Shared timestamp mixin ───────────────────────────────────

class TimestampMixin(BaseModel):
    """Shared timestamp fields for all response schemas."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
