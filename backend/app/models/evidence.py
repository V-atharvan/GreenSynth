"""
GreenSynth Analytics — Advanced Statistical Analysis & Evidence Layer ORM Models (Phase 15)

Defines:
  1. DatasetVersion: Versioned dataset snapshot (V1 -> V2) with explicit inclusion/exclusion rules.
  2. StatisticalModel: Registry for statistical linear, interaction, and quadratic models with fit metrics and diagnostics.
  3. ScientificMethod: Registry for versioned statistical and calculation methods.
  4. EvidenceRecord: Formal evidence-backed scientific observation record with conservative scientific language.
  5. EvidenceVersion: History record for versioned evidence statements.
  6. OutlierFlag: Outlier tracking entity that flags potential outliers without overwriting raw data.
  7. DataQualityReport: Data Quality Dashboard status record (PASS, WARNING, ERROR).
  8. ResearcherInterpretation: Peer notes separate from system-generated summaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DatasetVersion(Base):
    """
    Versioned snapshot of a scientific dataset (V1 -> V2).

    Records exact inclusion/exclusion rules, included samples, included DOE runs,
    filtering parameters, missing response counts, and dataset status.
    """

    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    included_sample_ids: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    included_experiment_ids: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    included_doe_run_ids: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=list
    )
    included_factors: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    included_responses: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )

    filtering_rules: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    exclusion_rules: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    summary_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="ACTIVE",
        comment="DRAFT, ACTIVE, ML_READY, OPTIMIZATION_READY, ARCHIVED",
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset")  # type: ignore[name-defined]
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship(
        "EvidenceRecord", back_populates="dataset_version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DatasetVersion id={self.id!s} version={self.version!r} status={self.status!r}>"


class StatisticalModel(Base):
    """
    Registry entity for fitted statistical models (Linear, Interaction, Quadratic).
    """

    __tablename__ = "statistical_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    model_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SIMPLE_LINEAR, MULTIPLE_LINEAR, INTERACTION, QUADRATIC"
    )
    formula: Mapped[str] = mapped_column(String(255), nullable=False)
    response_property: Mapped[str] = mapped_column(String(128), nullable=False)
    predictors: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )

    coefficients_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    metrics_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    diagnostics_json: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT", comment="DRAFT, VALIDATED, REJECTED, ARCHIVED"
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<StatisticalModel id={self.id!s} formula={self.formula!r} status={self.status!r}>"


class ScientificMethod(Base):
    """
    Scientific Method Registry storing versioned statistical and scientific methods.
    """

    __tablename__ = "scientific_methods"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    formula_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    limitations: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ScientificMethod name={self.name!r} version={self.version!r}>"


class EvidenceRecord(Base):
    """
    Evidence-backed scientific observation record with conservative scientific language.
    """

    __tablename__ = "evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="OBSERVATION, ASSOCIATION, STATISTICAL_EFFECT, MODEL_ESTIMATE, VALIDATED_RESULT",
    )
    variables: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    sample_size: Mapped[int] = mapped_column(nullable=False)
    statistical_method: Mapped[str] = mapped_column(String(128), nullable=False)

    effect_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_interval: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    prediction_interval: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    evidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scoring_criteria: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    limitations: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT", comment="DRAFT, APPROVED, REJECTED, ARCHIVED"
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    dataset_version: Mapped[DatasetVersion] = relationship(
        "DatasetVersion", back_populates="evidence_records"
    )
    interpretations: Mapped[list["ResearcherInterpretation"]] = relationship(
        "ResearcherInterpretation", back_populates="evidence_record", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EvidenceRecord id={self.id!s} type={self.evidence_type!r} score={self.evidence_score}>"


class OutlierFlag(Base):
    """
    Outlier tracking entity that flags potential outliers without overwriting raw data.
    """

    __tablename__ = "outlier_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=True,
    )

    variable_name: Mapped[str] = mapped_column(String(128), nullable=False)
    original_value: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, comment="IQR, Z_SCORE")
    threshold: Mapped[float] = mapped_column(Float, nullable=False)

    is_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)

    researcher_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<OutlierFlag variable={self.variable_name!r} val={self.original_value} excluded={self.is_excluded}>"


class DataQualityReport(Base):
    """
    Data Quality Dashboard report record.
    """

    __tablename__ = "data_quality_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")

    quality_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PASS", comment="PASS, WARNING, ERROR"
    )
    metrics_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    warnings_json: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<DataQualityReport status={self.quality_status!r} warnings={len(self.warnings_json)}>"


class ResearcherInterpretation(Base):
    """
    Researcher qualitative notes separate from system-generated text.
    """

    __tablename__ = "researcher_interpretations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    researcher_name: Mapped[str] = mapped_column(String(255), nullable=False)
    interpretation_notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    evidence_record: Mapped[EvidenceRecord] = relationship(
        "EvidenceRecord", back_populates="interpretations"
    )

    def __repr__(self) -> str:
        return f"<ResearcherInterpretation researcher={self.researcher_name!r}>"
