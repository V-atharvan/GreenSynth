"""
GreenSynth Analytics — Validation ORM Models

Defines:
  1. ValidationCriterion: Researcher-defined validation criteria & acceptable error thresholds.
  2. HoldoutValidation: Record of holdout experiment validation (intentionally excluded from training).
  3. ProspectiveExperiment: Model prediction accepted by researcher for physical lab synthesis.
  4. ValidationResult: Comparison record between model prediction & actual laboratory characterization.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ValidationCriterion(Base):
    """
    Researcher-defined criterion for validating property predictions against physical experiment results.
    """

    __tablename__ = "validation_criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="ABSOLUTE_ERROR, RELATIVE_ERROR, WITHIN_INTERVAL"
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    comparison_operator: Mapped[str] = mapped_column(
        String(8), nullable=False, default="<=", comment="<=, >=, =="
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ValidationCriterion id={self.id!s} prop={self.property_name!r} {self.comparison_operator} {self.threshold}>"


class HoldoutValidation(Base):
    """
    Holdout prediction validation record for experiments intentionally excluded from model training.
    """

    __tablename__ = "holdout_validations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    target_property: Mapped[str] = mapped_column(String(128), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)

    error: Mapped[float] = mapped_column(Float, nullable=False)
    absolute_error: Mapped[float] = mapped_column(Float, nullable=False)
    relative_error: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="COMPLETED", comment="COMPLETED, FAILED_LEAKAGE, TARGET_MISMATCH"
    )
    researcher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<HoldoutValidation id={self.id!s} model={self.model_id!s} abs_err={self.absolute_error:.4f}>"


class ProspectiveExperiment(Base):
    """
    Tracks a model prediction explicitly approved by a researcher for laboratory synthesis.
    """

    __tablename__ = "prospective_experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    proposed_conditions: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    researcher: Mapped[str | None] = mapped_column(String(255), nullable=True)

    approval_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        comment="PENDING, APPROVED, REJECTED, IN_LAB, COMPLETED",
    )

    laboratory_experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sample_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actual_result: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    measurement_uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)

    validation_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", comment="PENDING, COMPLETE, INCOMPLETE"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel")  # type: ignore[name-defined]
    prediction: Mapped["MLPrediction"] = relationship("MLPrediction")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<ProspectiveExperiment id={self.id!s} status={self.approval_status!r}>"


class ValidationResult(Base):
    """
    Final comparison record between model prediction & actual laboratory characterization.
    """

    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_candidates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
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
    dataset_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    target_property: Mapped[str] = mapped_column(String(128), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)

    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value_source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actual_measurement_uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)

    error: Mapped[float] = mapped_column(Float, nullable=False)
    signed_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_error: Mapped[float] = mapped_column(Float, nullable=False)
    relative_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_within_prediction_interval: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    criterion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_criteria.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    criterion_result: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="SATISFIED, NOT_SATISFIED"
    )

    validation_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PROSPECTIVE", comment="HOLDOUT, PROSPECTIVE, REPLICATE, RETROSPECTIVE"
    )
    validation_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="VALIDATED", comment="PENDING, READY_FOR_VALIDATION, VALIDATED, PARTIALLY_VALIDATED, FAILED, INVALID_DATA, REQUIRES_REVIEW"
    )
    validation_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_level: Mapped[str | None] = mapped_column(String(32), nullable=True, default="MODERATE")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    researcher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel")  # type: ignore[name-defined]
    criterion: Mapped[ValidationCriterion | None] = relationship("ValidationCriterion")

    def __repr__(self) -> str:
        return (
            f"<ValidationResult id={self.id!s} type={self.validation_type!r} "
            f"pred={self.predicted_value:.2f} act={self.actual_value:.2f} status={self.validation_status!r}>"
        )


class DatasetCandidate(Base):
    """
    Candidate experiment/sample result proposed for inclusion in future training datasets.
    Requires researcher review before entering a new dataset version.
    """

    __tablename__ = "dataset_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_dataset_id: Mapped[str] = mapped_column(String(64), nullable=False, default="cand_v1")
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    validation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposed_target: Mapped[str] = mapped_column(String(128), nullable=False)

    data_quality_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="VALID", comment="VALID, REQUIRES_REVIEW, INVALID"
    )
    researcher_review_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING_REVIEW",
        comment="PENDING_REVIEW, ACCEPTED, REJECTED, FLAGGED_FOR_REVIEW",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DatasetCandidate id={self.id!s} status={self.researcher_review_status!r}>"


class ModelPerformanceSnapshot(Base):
    """
    Performance snapshot of a model evaluation across training, cross-validation, test, or prospective validation.
    """

    __tablename__ = "model_performance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="TRAINING, CROSS_VALIDATION, TEST, PROSPECTIVE_VALIDATION, FULL_VALIDATION",
    )
    target_property: Mapped[str] = mapped_column(String(128), nullable=False)

    sample_count: Mapped[int] = mapped_column(nullable=False)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    r2: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_error: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ModelPerformanceSnapshot model={self.model_version} type={self.evaluation_type} n={self.sample_count}>"


class RecommendationOutcome(Base):
    """
    Outcome classification of a model recommendation tested in laboratory synthesis.
    """

    __tablename__ = "recommendation_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="OUTCOME_PENDING",
        comment="OUTCOME_PENDING, SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, INCONCLUSIVE",
    )
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<RecommendationOutcome id={self.id!s} outcome={self.outcome!r}>"


class ParameterDeviation(Base):
    """
    Comparison between RECOMMENDED, PLANNED, and ACTUAL synthesis parameters.
    """

    __tablename__ = "parameter_deviations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False)
    recommended_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    absolute_deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ParameterDeviation param={self.parameter_name!r} rec={self.recommended_value} act={self.actual_value}>"

