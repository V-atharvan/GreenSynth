"""
GreenSynth Analytics — Sample ORM Model

A Sample represents a physical specimen produced during an Experiment.
One experiment may produce multiple samples (e.g., different substrates).

Characterisation data (XRD, UV-Vis, etc.) will be linked to samples
in Phase 5 and later.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SampleStatus(str, enum.Enum):
    """Lifecycle status of a laboratory sample."""

    PREPARED = "PREPARED"
    READY_FOR_CHARACTERIZATION = "READY_FOR_CHARACTERIZATION"
    UNDER_ANALYSIS = "UNDER_ANALYSIS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Sample(Base):
    """
    Physical laboratory sample record.

    Each sample is produced by one Experiment.
    Characterisation records (XRD, UV-Vis, FTIR, SEM, Electrical)
    will be linked to samples in later development phases.
    """

    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Parent experiment ──────────────────────────────────
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ── Identification ────────────────────────────────────
    sample_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="Human-readable unique code, e.g. P7-EXP-001-S1"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Sample properties ─────────────────────────────────
    material: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="e.g. CuO"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=SampleStatus.PREPARED.value,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps (UTC) ───────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ──────────────────────────────────────
    experiment: Mapped["Experiment"] = relationship(  # type: ignore[name-defined]
        "Experiment", back_populates="samples"
    )

    def __repr__(self) -> str:
        return f"<Sample id={self.id!s} code={self.sample_code!r} status={self.status!r}>"
