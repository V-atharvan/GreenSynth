"""
GreenSynth Analytics — Experiment ORM Model

An Experiment represents a single synthesis run performed in the laboratory
under a specific set of synthesis parameters.

Each experiment belongs to one Project and can produce one or more Samples.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ExperimentStatus(str, enum.Enum):
    """Lifecycle status of a single laboratory experiment."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class Experiment(Base):
    """
    Laboratory experiment record.

    Stores metadata about a single synthesis run.
    Synthesis parameters and characterisation data are stored
    in separate tables (added in later phases).
    """

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Parent project ─────────────────────────────────────
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ── Identification ────────────────────────────────────
    experiment_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="Human-readable unique code, e.g. P7-EXP-001"
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)

    # ── Status ────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ExperimentStatus.PLANNED.value,
        index=True,
    )

    # ── Experimental details ───────────────────────────────
    experiment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    researcher: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Name of the researcher who conducted this experiment"
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
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="experiments"
    )
    samples: Mapped[list["Sample"]] = relationship(  # type: ignore[name-defined]
        "Sample", back_populates="experiment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Experiment id={self.id!s} code={self.experiment_code!r} "
            f"status={self.status!r}>"
        )
