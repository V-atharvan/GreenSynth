"""
GreenSynth Analytics — Characterization & RawFile Pydantic Schemas

Validation schemas and technique-to-allowed-format mappings.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TechniqueType(StrEnum):
    XRD = "XRD"
    UV_VIS = "UV_VIS"
    FTIR = "FTIR"
    SEM = "SEM"
    ELECTRICAL = "ELECTRICAL"


class CharacterizationStatus(StrEnum):
    UPLOADED = "UPLOADED"
    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    ARCHIVED = "ARCHIVED"


# ── Allowed file extension mappings per technique ───────────
TECHNIQUE_ALLOWED_EXTENSIONS: dict[TechniqueType, set[str]] = {
    TechniqueType.XRD: {"csv", "txt", "xlsx", "json"},
    TechniqueType.UV_VIS: {"csv", "txt", "xlsx", "json"},
    TechniqueType.FTIR: {"csv", "txt", "xlsx", "json"},
    TechniqueType.ELECTRICAL: {"csv", "txt", "xlsx", "json"},
    TechniqueType.SEM: {"png", "jpg", "jpeg", "tiff", "tif", "pdf"},
}


# ── Characterization Schemas ────────────────────────────────

class CharacterizationBase(BaseModel):
    technique: TechniqueType
    characterization_date: datetime | None = None
    operator: str | None = Field(default=None, max_length=255)
    instrument_name: str | None = Field(default=None, max_length=255)
    instrument_model: str | None = Field(default=None, max_length=255)
    instrument_id: str | None = Field(default=None, max_length=128)
    notes: str | None = None


class CharacterizationCreate(CharacterizationBase):
    sample_id: UUID


class CharacterizationUpdate(BaseModel):
    characterization_date: datetime | None = None
    operator: str | None = Field(default=None, max_length=255)
    instrument_name: str | None = Field(default=None, max_length=255)
    instrument_model: str | None = Field(default=None, max_length=255)
    instrument_id: str | None = Field(default=None, max_length=128)
    notes: str | None = None
    status: CharacterizationStatus | None = None


class RawFileResponse(BaseModel):
    id: UUID
    characterization_id: UUID
    sample_id: UUID
    original_filename: str
    stored_filename: str
    file_extension: str
    mime_type: str | None
    file_size: int
    checksum: str
    storage_path: str
    uploaded_at: datetime
    uploaded_by: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class CharacterizationResponse(CharacterizationBase):
    id: UUID
    sample_id: UUID
    status: CharacterizationStatus
    raw_files: list[RawFileResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
