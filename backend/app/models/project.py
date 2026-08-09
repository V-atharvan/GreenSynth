"""
GreenSynth Analytics — Project ORM Model

A Project represents one synthesis research program (e.g., Project 7: CuO spray pyrolysis).
Projects are defined by configuration metadata — no experimental data lives here.

Projects are designed to be configuration-driven (see configs/projects/).
Do NOT hard-code Project 7 logic into business logic modules.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectStatus(str, enum.Enum):
    """Lifecycle status of a research project."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Project(Base):
    """
    Research project record.

    Each project represents a distinct synthesis approach (material + extract +
    solvent + method combination).  The eight planned projects are:

    P1: CuO + Mulberry + Ethanol   + Sol-gel
    P2: CuO + Mulberry + Acetone   + Sol-gel
    P3: CuO + Mulberry + Ethanol   + Hydrothermal
    P4: CuO + Mulberry + Acetone   + Hydrothermal
    P5: Si  + Rice husk + Ethanol  + Hydrothermal
    P6: Si  + Rice husk + Acetone  + Hydrothermal
    P7: CuO + Mulberry + Ethanol   + Spray Pyrolysis  ← MVP
    P8: CuO + Mulberry + Acetone   + Spray Pyrolysis

    This model stores ONLY configuration metadata.
    Experimental data is stored in Experiment and Sample records.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True,
        comment="Short unique code, e.g. P7"
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Synthesis identity ─────────────────────────────────
    material: Mapped[str] = mapped_column(String(128), nullable=False, comment="e.g. CuO")
    extract: Mapped[str] = mapped_column(String(128), nullable=False, comment="e.g. Mulberry")
    solvent: Mapped[str] = mapped_column(String(128), nullable=False, comment="e.g. Ethanol")
    synthesis_method: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="e.g. Spray Pyrolysis"
    )

    # ── Status ────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProjectStatus.ACTIVE.value, index=True
    )

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
    experiments: Mapped[list["Experiment"]] = relationship(  # type: ignore[name-defined]
        "Experiment", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id!s} code={self.project_code!r} name={self.name!r}>"
