"""
GreenSynth Analytics — Phase 18 Evidence-Based Optimization ORM Models

Defines:
  1. OptimizationObjective: Researcher optimization goal definition (MAXIMIZE, MINIMIZE, TARGET) with target property & weight.
  2. OptimizationConstraint: Parameter/property bounds (PARAMETER_RANGE, PROPERTY_RANGE, FIXED_VALUE, CATEGORICAL_ALLOWED_VALUE, MODEL_DOMAIN).
  3. OptimizationSearchSpace: Project search space definition containing parameter boundaries, step sizes, and constraints.
  4. OptimizationRun: Optimization execution session (PLANNED, RUNNING, COMPLETED, FAILED, CANCELLED).
  5. OptimizationCandidate: Individually scored and ranked candidate condition (GENERATED, SHORTLISTED, SELECTED, REJECTED, CONVERTED_TO_EXPERIMENT, ARCHIVED).
  6. CandidatePrediction: Link between candidate parameters and model prediction engine output.
  7. CandidateExperimentLink: Traceable audit link between candidate and created proposed experiment.
  8. CandidateEvidenceSnapshot: Immutable snapshot of model version, dataset version, validation metrics, and domain status.
  9. OptimizationReview: Researcher review audit log (SELECTED, REJECTED, DEFERRED, reason, notes).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OptimizationObjective(Base):
    """
    Researcher-defined optimization objective.
    Direction: MAXIMIZE, MINIMIZE, TARGET.
    """

    __tablename__ = "optimization_objectives"

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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_property: Mapped[str] = mapped_column(String(128), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="MAXIMIZE, MINIMIZE, TARGET"
    )
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE", comment="ACTIVE, ARCHIVED"
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<OptimizationObjective id={self.id!s} name={self.name!r} direction={self.direction!r}>"


class OptimizationConstraint(Base):
    """
    Search-space constraint for parameters or properties.
    """

    __tablename__ = "optimization_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    constraint_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="PARAMETER_RANGE, PROPERTY_RANGE, FIXED_VALUE, CATEGORICAL_ALLOWED_VALUE, MODEL_DOMAIN",
    )
    target_code: Mapped[str] = mapped_column(String(128), nullable=False)
    operator: Mapped[str] = mapped_column(String(32), nullable=False, default="BETWEEN")

    minimum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    fixed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    allowed_values: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_hard_constraint: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    penalty_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<OptimizationConstraint id={self.id!s} type={self.constraint_type!r} target={self.target_code!r}>"


class OptimizationSearchSpace(Base):
    """
    Generated search space combining project parameters, defined ranges, and constraints.
    """

    __tablename__ = "optimization_search_spaces"

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

    parameters_definition: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    constraints_definition: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OptimizationRun(Base):
    """
    Optimization execution session record.
    """

    __tablename__ = "optimization_runs"

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
        ForeignKey("optimization_objectives.id", ondelete="CASCADE"),
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
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)

    generation_method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="RANDOM_SEARCH", comment="GRID_SEARCH, RANDOM_SEARCH, MODEL_GUIDED_SEARCH"
    )
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requested_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    feasible_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    search_space_definition: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    constraints_definition: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PLANNED",
        comment="PLANNED, RUNNING, COMPLETED, FAILED, CANCELLED",
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    candidates: Mapped[list["OptimizationCandidate"]] = relationship(
        "OptimizationCandidate",
        back_populates="optimization_run",
        cascade="all, delete-orphan",
        order_by="OptimizationCandidate.rank",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OptimizationRun id={self.id!s} status={self.status!r} method={self.generation_method!r}>"


class OptimizationCandidate(Base):
    """
    Individually evaluated candidate synthesis condition.
    """

    __tablename__ = "optimization_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    optimization_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    parameter_values: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    parameter_units: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    feasibility_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="FEASIBLE", comment="FEASIBLE, INFEASIBLE, WARNING"
    )
    domain_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="IN_DOMAIN", comment="IN_DOMAIN, NEAR_BOUNDARY, OUT_OF_DOMAIN"
    )

    predictions: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    uncertainties: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    objective_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_breakdown: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    novelty_category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="LOW_DISTANCE", comment="LOW_DISTANCE, MEDIUM_DISTANCE, HIGH_DISTANCE, ALREADY_TESTED"
    )
    parameter_distance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nearby_experiment_ids: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )

    candidate_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="EXPLOITATION", comment="EXPLOITATION, EXPLORATION"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="GENERATED",
        comment="GENERATED, SHORTLISTED, SELECTED, REJECTED, CONVERTED_TO_EXPERIMENT, ARCHIVED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    optimization_run: Mapped[OptimizationRun] = relationship(
        "OptimizationRun", back_populates="candidates"
    )

    def __repr__(self) -> str:
        return f"<OptimizationCandidate rank={self.rank} status={self.status!r} score={self.objective_score:.4f}>"


class CandidatePrediction(Base):
    """
    Explicit link between Candidate and Prediction output.
    """

    __tablename__ = "candidate_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CandidateExperimentLink(Base):
    """
    Traceability link from Optimization Candidate to created Experiment.
    """

    __tablename__ = "candidate_experiment_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PROPOSED_EXPERIMENT", comment="PROPOSED_EXPERIMENT, VALIDATION_EXPERIMENT"
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CandidateEvidenceSnapshot(Base):
    """
    Immutable evidence snapshot for a candidate.
    """

    __tablename__ = "candidate_evidence_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_metrics: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    supporting_experiment_ids: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    domain_status: Mapped[str] = mapped_column(String(32), nullable=False)
    uncertainty_method: Mapped[str] = mapped_column(String(64), nullable=False, default="Residual Variance / Confidence Interval")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OptimizationReview(Base):
    """
    Researcher review decision audit log.
    """

    __tablename__ = "optimization_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    optimization_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimization_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[str] = mapped_column(String(255), nullable=False, default="Researcher")
    decision: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="SELECTED, REJECTED, DEFERRED"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
