"""
GreenSynth Analytics — Machine Learning ORM Models

Defines:
  1. MLDataset: Versioned ML dataset definition referencing selected experiments, features, & target.
  2. MLDatasetRecord: Individual row with full provenance (experiment, sample, features, target, eligibility).
  3. MLTrainingRun: Reproducible training execution record (hyperparameters, CV metrics, warnings).
  4. MLModel: Model registry entry with artifact path, status lifecycle, and feature importance.
  5. MLPrediction: Traceable prediction record with uncertainty and applicability domain checks.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MLDataset(Base):
    """
    Versioned ML dataset definition.

    References selected experiments, samples, synthesis parameters, and target properties
    for machine learning training while preserving data provenance and immutability.
    """

    __tablename__ = "ml_datasets"

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

    target_property: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="MEASURED", comment="MEASURED or CALCULATED"
    )
    target_unit: Mapped[str] = mapped_column(String(32), nullable=False)

    # Features: [{"feature_name": "temp", "source_parameter": "substrate_temperature", "unit": "°C", "data_type": "NUMBER"}]
    features: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    # Filters applied during construction: {"synthesis_method": "Spray Pyrolysis"}
    filters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    # Preprocessing config: {"scaling": "STANDARD", "imputation": "NONE"}
    preprocessing_config: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT", comment="DRAFT, READY, IMMUTABLE, ARCHIVED"
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    eligible_count: Mapped[int] = mapped_column(nullable=False, default=0)
    excluded_count: Mapped[int] = mapped_column(nullable=False, default=0)
    exclusion_summary: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # type: ignore[name-defined]
    records: Mapped[list[MLDatasetRecord]] = relationship(
        "MLDatasetRecord", back_populates="dataset", cascade="all, delete-orphan"
    )
    training_runs: Mapped[list[MLTrainingRun]] = relationship(
        "MLTrainingRun", back_populates="dataset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLDataset id={self.id!s} name={self.name!r} v={self.version} target={self.target_property!r}>"


class MLDatasetRecord(Base):
    """
    Individual observation row in an ML dataset with complete scientific provenance.
    """

    __tablename__ = "ml_dataset_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
    analysis_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Feature Map: {"substrate_temperature": 350.0, "spray_rate": 3.0}
    feature_values: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="MISSING_FEATURE, MISSING_TARGET, INVALID_UNIT, OUTLIER, etc."
    )
    provenance_details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    dataset: Mapped[MLDataset] = relationship("MLDataset", back_populates="records")

    def __repr__(self) -> str:
        return f"<MLDatasetRecord id={self.id!s} exp={self.experiment_id!s} eligible={self.is_eligible}>"


class MLTrainingRun(Base):
    """
    Reproducible ML model training run execution log.
    """

    __tablename__ = "ml_training_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)

    model_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="MEAN_BASELINE, LINEAR_REGRESSION, RIDGE, RANDOM_FOREST, GRADIENT_BOOSTING"
    )
    preprocessing_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")

    hyperparameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    random_seed: Mapped[int] = mapped_column(nullable=False, default=42)
    cv_folds: Mapped[int] = mapped_column(nullable=False, default=5)
    split_ratio: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    training_metrics: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    validation_metrics: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    test_metrics: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    overfitting_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    low_data_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", comment="PENDING, RUNNING, COMPLETED, FAILED"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    dataset: Mapped[MLDataset] = relationship("MLDataset", back_populates="training_runs")
    models: Mapped[list[MLModel]] = relationship(
        "MLModel", back_populates="training_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLTrainingRun id={self.id!s} model_type={self.model_type!r} status={self.status!r}>"


class MLModel(Base):
    """
    Registered Machine Learning model metadata and artifact link.
    """

    __tablename__ = "ml_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    training_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_training_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")

    target_property: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False, default="MEASURED")
    target_unit: Mapped[str] = mapped_column(String(32), nullable=False)

    feature_names: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    feature_specs: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    preprocessing_config: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    hyperparameters: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    random_seed: Mapped[int] = mapped_column(nullable=False, default=42)

    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="SHA256 checksum of saved pipeline artifact")
    feature_ranges_json: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Feature training min, max, mean, std"
    )
    selection_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    metrics: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    feature_importance: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    library_versions: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="TRAINED",
        comment="TRAINED, VALIDATED, APPROVED, REJECTED, PRODUCTION_CANDIDATE, ARCHIVED",
    )
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    training_run: Mapped[MLTrainingRun] = relationship("MLTrainingRun", back_populates="models")
    predictions: Mapped[list[MLPrediction]] = relationship(
        "MLPrediction", back_populates="model", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLModel id={self.id!s} name={self.name!r} v={self.version} status={self.status!r}>"


class MLPrediction(Base):
    """
    Traceable machine learning prediction record.
    """

    __tablename__ = "ml_predictions"

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

    input_parameters: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    predicted_property: Mapped[str] = mapped_column(String(128), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)

    uncertainty_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_method: Mapped[str | None] = mapped_column(String(64), nullable=True)

    applicability_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="VALID",
        comment="VALID, CAUTION, OUT_OF_DOMAIN, INSUFFICIENT_DATA, MODEL_NOT_VALIDATED",
    )
    applicability_details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    warnings: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    model: Mapped[MLModel] = relationship("MLModel", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<MLPrediction id={self.id!s} property={self.predicted_property!r} "
            f"value={self.predicted_value:.4f} status={self.applicability_status!r}>"
        )
