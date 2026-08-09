"""
GreenSynth Analytics — Machine Learning Validation & Monitoring ORM Models (Phase 17)

Defines:
  1. PredictionValidation: Traceable record comparing an ML model prediction against an actual laboratory measurement.
  2. ExperimentPredictionLink: Permanent traceable relationship linking a prediction to an experiment.
  3. ConditionDeviation: Parameter synthesis condition comparison (predicted vs actual synthesis parameters).
  4. ModelPerformanceSnapshot: Immutable model health and error snapshot over validation history.
  5. ModelMonitoringEvent: Monitoring event log for dataset shift, bias, and performance warnings.
  6. ModelReview: Audit entity for researcher model reviews and lifecycle transitions.
  7. MLReadinessCheck: Audit log entity for dataset ML readiness check evaluations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PredictionValidation(Base):
    """
    Validation record comparing an ML model prediction against an actual laboratory experiment measurement.
    """

    __tablename__ = "prediction_validations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
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

    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dataset_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    target_property: Mapped[str] = mapped_column(String(128), nullable=False, default="conductivity_s_cm")
    target_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="S/cm")

    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)

    error: Mapped[float] = mapped_column(Float, nullable=False, comment="actual - predicted (signed error)")
    absolute_error: Mapped[float] = mapped_column(Float, nullable=False, comment="abs(actual - predicted)")
    relative_error: Mapped[float | None] = mapped_column(Float, nullable=True, comment="abs(actual - predicted) / abs(actual)")
    percentage_error: Mapped[float | None] = mapped_column(Float, nullable=True, comment="abs(actual - predicted) / abs(actual) * 100")

    actual_inside_interval: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="Whether actual falls inside prediction uncertainty interval")

    validation_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="VALIDATED", comment="PENDING, VALIDATED, INVALID, REJECTED"
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="MEASURED_PROPERTY", comment="MANUAL, CALCULATED_PROPERTY, MEASURED_PROPERTY"
    )
    is_target_calculated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quality_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="VALID", comment="VALID, VALID_WITH_WARNING, INVALID"
    )
    conversion_details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Unit conversion factor and units if converted"
    )

    validated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    prediction: Mapped["MLPrediction"] = relationship("MLPrediction")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<PredictionValidation id={self.id!s} pred={self.predicted_value:.4f} "
            f"actual={self.actual_value:.4f} err={self.error:.4f} status={self.validation_status!r}>"
        )


class ExperimentPredictionLink(Base):
    """
    Traceable link between a prediction and a laboratory experiment.
    """

    __tablename__ = "experiment_prediction_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="CASCADE"),
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
        String(64), nullable=False, default="PREDICTION_VALIDATION", comment="PREDICTION_VALIDATION or PREDICTION_DERIVED_EXPERIMENT"
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ExperimentPredictionLink id={self.id!s} pred={self.prediction_id!s} exp={self.experiment_id!s}>"


class ConditionDeviation(Base):
    """
    Comparison between predicted synthesis conditions and actual laboratory experiment conditions.
    """

    __tablename__ = "condition_deviations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_predictions.id", ondelete="CASCADE"),
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
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)

    absolute_deviation: Mapped[float] = mapped_column(Float, nullable=False, comment="abs(actual - predicted)")
    relative_deviation: Mapped[float | None] = mapped_column(Float, nullable=True, comment="abs(actual - predicted) / abs(predicted)")
    tolerance: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="EXACT_MATCH", comment="EXACT_MATCH, MINOR_DEVIATION, MAJOR_DEVIATION"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ConditionDeviation param={self.parameter_name!r} dev={self.absolute_deviation:.2f} status={self.status!r}>"


class ModelHealthSnapshot(Base):
    """
    Immutable snapshot of aggregated model validation metrics over time.
    """

    __tablename__ = "model_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")

    validation_count: Mapped[int] = mapped_column(nullable=False, default=0)
    mae: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rmse: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    r2: Mapped[float | None] = mapped_column(Float, nullable=True)

    mean_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="Signed mean error for prediction bias detection")
    median_absolute_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    interval_coverage: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Fraction of actuals falling inside prediction uncertainty intervals")

    out_of_range_count: Mapped[int] = mapped_column(nullable=False, default=0)
    dataset_shift_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    performance_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="INSUFFICIENT_DATA", comment="INSUFFICIENT_DATA, STABLE, WARNING, DEGRADED, CRITICAL"
    )

    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ModelHealthSnapshot model={self.model_id!s} count={self.validation_count} MAE={self.mae:.4f} status={self.performance_status!r}>"


class ModelMonitoringEvent(Base):
    """
    Log event recording model health degradation, dataset shift, or out-of-domain warnings.
    """

    __tablename__ = "model_monitoring_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")

    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="PERFORMANCE_DEGRADATION, DATASET_SHIFT, PREDICTION_BIAS, OUT_OF_DOMAIN, INSUFFICIENT_VALIDATION_DATA"
    )
    severity: Mapped[str] = mapped_column(
        String(32), nullable=False, default="INFO", comment="INFO, WARNING, CRITICAL"
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ModelMonitoringEvent type={self.event_type!r} severity={self.severity!r}>"


class ModelReview(Base):
    """
    Audit record for researcher model reviews, status evaluation, or model retirement.
    """

    __tablename__ = "model_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="REVIEWED", comment="REVIEWED, REQUIRES_INVESTIGATION, ACCEPTED, REJECTED, RETIRED"
    )
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ModelReview model={self.model_id!s} status={self.review_status!r} reviewer={self.reviewer!r}>"


class MLReadinessCheck(Base):
    """
    Log entity recording ML_READY dataset validation evaluations.
    """

    __tablename__ = "ml_readiness_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="READY", comment="READY, NOT_READY, READY_WITH_WARNING"
    )

    criteria_results_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    reasons_json: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<MLReadinessCheck id={self.id!s} status={self.status!r}>"
