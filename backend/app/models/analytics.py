"""
GreenSynth Analytics — Sample Comparison & Statistical Analysis ORM Models

Defines:
  1. Dataset: Logical comparison dataset definition referencing selected samples & variables
  2. StatisticalAnalysis: Traceable statistical execution record (Descriptive, Correlation, Linear Regression, Group Comparison, Outliers)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Dataset(Base):
    """
    Logical comparison dataset definition.

    References selected experiments, samples, synthesis parameters,
    and calculated properties without copying raw data.
    """

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Selected Sample IDs: ["uuid1", "uuid2", ...]
    sample_ids: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    # Selected Variables: ["substrate_temperature", "spray_rate", "band_gap_ev", "conductivity_s_cm"]
    variables: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    # Applied Filters: {"synthesis_method": "Spray Pyrolysis", "temp_min": 250}
    filters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # type: ignore[name-defined]
    statistical_analyses: Mapped[list[StatisticalAnalysis]] = relationship(
        "StatisticalAnalysis", back_populates="dataset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id!s} name={self.name!r} samples_count={len(self.sample_ids)}>"


class StatisticalAnalysis(Base):
    """
    Traceable statistical execution record.

    Stores independent & dependent variables, statistical test method,
    calculated results (mean, r, slope, R^2, p-value), warnings, and assumptions.
    """

    __tablename__ = "statistical_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    analysis_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="DESCRIPTIVE, CORRELATION, REGRESSION, GROUP_COMPARISON, OUTLIERS"
    )
    x_variable: Mapped[str | None] = mapped_column(String(128), nullable=True)
    y_variable: Mapped[str | None] = mapped_column(String(128), nullable=True)
    group_variable: Mapped[str | None] = mapped_column(String(128), nullable=True)

    method: Mapped[str] = mapped_column(String(128), nullable=False, comment="e.g. Pearson Correlation, Ordinary Least Squares")
    sample_size: Mapped[int] = mapped_column(nullable=False)

    results_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    assumptions_json: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    warnings_json: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="statistical_analyses")

    def __repr__(self) -> str:
        return (
            f"<StatisticalAnalysis id={self.id!s} type={self.analysis_type!r} "
            f"x={self.x_variable!r} y={self.y_variable!r} n={self.sample_size}>"
        )
