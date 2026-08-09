"""
GreenSynth Analytics — Recommendation ORM Models

Defines:
  1. Recommendation: Stores decision support recommendation sessions generated for an objective & model.
  2. RecommendationCandidate: Individually ranked candidate experimental conditions with evidence, domain status,
     objective scores, uncertainty bounds, and human-in-the-loop researcher review statuses.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Recommendation(Base):
    """
    Recommendation session record linking Project, Objective, Validated Model, and Dataset.
    """

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    objective_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("objectives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    researcher: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="GENERATED",
        comment="DRAFT, GENERATED, UNDER_REVIEW, APPROVED, REJECTED, EXPERIMENT_CREATED, VALIDATED, ARCHIVED",
    )
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    ranking_method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="BALANCED", comment="BALANCED, EXPLOITATION, EXPLORATION"
    )
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    candidates: Mapped[list["RecommendationCandidate"]] = relationship(
        "RecommendationCandidate",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="RecommendationCandidate.rank",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id!s} status={self.status!r} candidates={self.candidate_count}>"


class RecommendationCandidate(Base):
    """
    Individually scored and ranked candidate experimental condition.
    """

    __tablename__ = "recommendation_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    parameter_set: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    predicted_properties: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    uncertainty: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    applicability_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="IN_DOMAIN", comment="IN_DOMAIN, OUT_OF_DOMAIN, NEAR_BOUNDARY"
    )
    evidence_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MODERATE", comment="HIGH, MODERATE, LOW"
    )
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    objective_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    constraint_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="SATISFIED", comment="SATISFIED, SOFT_VIOLATION, HARD_VIOLATION"
    )
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="GENERATED",
        comment="GENERATED, UNDER_REVIEW, APPROVED, REJECTED, MODIFIED, EXPERIMENT_CREATED, VALIDATED",
    )

    modified_parameter_set: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    modification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    recommendation: Mapped[Recommendation] = relationship(
        "Recommendation", back_populates="candidates"
    )

    def __repr__(self) -> str:
        return f"<RecommendationCandidate rank={self.rank} status={self.status!r} score={self.overall_score:.4f}>"
