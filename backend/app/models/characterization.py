"""
GreenSynth Analytics — Characterization & RawFile ORM Models

Defines:
  1. Characterization: Laboratory measurement metadata (Technique, Instrument, Date, Operator).
  2. RawFile: Immutable raw dataset file record linked to Characterization and Sample.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TechniqueType(str, enum.Enum):
    XRD = "XRD"
    UV_VIS = "UV_VIS"
    FTIR = "FTIR"
    SEM = "SEM"
    ELECTRICAL = "ELECTRICAL"


class CharacterizationStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    ARCHIVED = "ARCHIVED"


class RawFileStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Characterization(Base):
    """
    Laboratory characterization run record.

    Links physical Sample to raw laboratory measurement files.
    """

    __tablename__ = "characterizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    technique: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="XRD, UV_VIS, FTIR, SEM, ELECTRICAL"
    )
    characterization_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    operator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instrument_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instrument_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instrument_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CharacterizationStatus.UPLOADED.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    sample: Mapped["Sample"] = relationship(  # type: ignore[name-defined]
        "Sample", backref="characterizations"
    )
    raw_files: Mapped[list["RawFile"]] = relationship(
        "RawFile", back_populates="characterization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Characterization id={self.id!s} technique={self.technique!r} "
            f"sample_id={self.sample_id!s} status={self.status!r}>"
        )


class RawFile(Base):
    """
    Immutable raw laboratory file record.

    Stores SHA-256 checksum, original filename, storage path, file size,
    and metadata for complete scientific traceability.
    """

    __tablename__ = "raw_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    characterization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characterizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="File size in bytes")
    checksum: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="SHA-256 checksum"
    )
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_metadata: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Extra metadata extracted on upload"
    )

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RawFileStatus.ACTIVE.value, index=True
    )

    # Relationships
    characterization: Mapped[Characterization] = relationship(
        "Characterization", back_populates="raw_files"
    )
    sample: Mapped["Sample"] = relationship("Sample")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<RawFile id={self.id!s} name={self.original_filename!r} "
            f"checksum={self.checksum[:8]}... size={self.file_size}B>"
        )
