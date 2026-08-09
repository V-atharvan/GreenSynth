"""
GreenSynth Analytics — Objective Definition & Design of Experiments (DOE) ORM Models (Phase 14 Extended)

Defines:
  1. Objective: Formally specifies optimization goals (MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE),
     weights, target material properties, and synthesis constraints.
  2. DOE (and alias DOEStudy): Design of Experiments configuration (Full Factorial, Fractional Factorial, CCD, Box-Behnken, Random),
     factors, ranges, responses, replicates, center points, random seed, versioning, and status lifecycle.
  3. ProposedExperiment (and alias DOEDesignRun): Systematically proposed experimental conditions awaiting researcher review & approval,
     run order, replicate numbers, center point indicators, and linked measured responses.
  4. DOEAnalysis: Factor main effects, interaction effects, response surface regression fit metrics, and residual diagnostics.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Objective(Base):
    """
    Formal optimization objective definition.

    Distinguishes target property, optimization direction (MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE),
    acceptable ranges, weights, and synthesis parameter constraints.
    """

    __tablename__ = "objectives"

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
    direction: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE"
    )
    target_value: Mapped[float | None] = mapped_column(nullable=True)
    min_value: Mapped[float | None] = mapped_column(nullable=True)
    max_value: Mapped[float | None] = mapped_column(nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weight: Mapped[float] = mapped_column(nullable=False, default=1.0)

    synthesis_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    solvent: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Constraints: [{"parameter": "substrate_temperature", "operator": "BETWEEN", "value": [250, 400], "unit": "°C"}]
    constraints: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT", comment="DRAFT, ACTIVE, ARCHIVED"
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # type: ignore[name-defined]
    does: Mapped[list[DOE]] = relationship(
        "DOE", back_populates="objective", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Objective id={self.id!s} name={self.name!r} direction={self.direction!r} status={self.status!r}>"


class DOE(Base):
    """
    Design of Experiments (DOE) configuration (DOEStudy).

    Stores research question, controllable experimental factors, response definitions,
    design method (FULL_FACTORIAL, FRACTIONAL_FACTORIAL, CENTRAL_COMPOSITE, BOX_BEHNKEN, RANDOMIZED_CANDIDATE),
    replication count, center points, random seed, design resolution, versioning (V1, V2), and status lifecycle.
    """

    __tablename__ = "does"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    objective_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("objectives.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")

    design_method: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="FULL_FACTORIAL, FRACTIONAL_FACTORIAL, CENTRAL_COMPOSITE, BOX_BEHNKEN, RANDOMIZED_CANDIDATE",
    )

    # Factors: [{"parameter_code": "temp", "name": "Substrate Temp", "role": "CONTROLLABLE", "factor_type": "CONTINUOUS", "lower_bound": 300, "upper_bound": 400, "unit": "°C"}]
    factors: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    # Responses: [{"property_name": "Electrical Conductivity", "unit": "S/cm", "direction": "MAXIMIZE", "weight": 1.0}]
    responses: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, default=list
    )
    # Applied Constraints: [{"parameter_code": "spray_rate", "operator": "<=", "value": 5}]
    constraints: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    requested_runs: Mapped[int] = mapped_column(nullable=False, default=1)
    replicates: Mapped[int] = mapped_column(nullable=False, default=1)
    center_points: Mapped[int] = mapped_column(nullable=False, default=0)
    alpha_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    design_resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)

    random_seed: Mapped[int | None] = mapped_column(nullable=True, default=42)
    randomize_run_order: Mapped[bool] = mapped_column(nullable=False, default=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="GENERATED",
        comment="DRAFT, CONFIGURED, GENERATED, UNDER_REVIEW, APPROVED, PARTIALLY_EXECUTED, COMPLETED, ARCHIVED",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    objective: Mapped[Objective | None] = relationship("Objective", back_populates="does")
    proposed_experiments: Mapped[list[ProposedExperiment]] = relationship(
        "ProposedExperiment", back_populates="doe", cascade="all, delete-orphan"
    )
    analyses: Mapped[list[DOEAnalysis]] = relationship(
        "DOEAnalysis", back_populates="doe", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DOE id={self.id!s} name={self.name!r} method={self.design_method!r} version={self.version!r}>"


class ProposedExperiment(Base):
    """
    Proposed experimental condition generated by DOE (DOEDesignRun).

    A DOE condition is NOT an actual result. It awaits researcher review & approval
    before being converted into a PLANNED experiment.
    """

    __tablename__ = "proposed_experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("does.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    design_condition_id: Mapped[str] = mapped_column(String(64), nullable=False)

    design_order: Mapped[int] = mapped_column(nullable=False)
    run_order: Mapped[int] = mapped_column(nullable=False)
    replicate_number: Mapped[int] = mapped_column(nullable=False, default=1)
    is_center_point: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    block: Mapped[str | None] = mapped_column(String(64), nullable=True, default="Block_1")

    # Factor values map: {"substrate_temperature": 325.0, "spray_rate": 3.0}
    factor_values: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    # Measured responses map: {"Electrical Conductivity": 5.10, "Band Gap": 1.45}
    measured_responses: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    # Measured parameter deviations: {"substrate_temperature": {"proposed": 350.0, "actual": 357.0, "deviation": 7.0}}
    parameter_deviations: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PROPOSED",
        comment="PROPOSED, APPROVED, REJECTED, PLANNED, IN_PROGRESS, COMPLETED, FAILED, SKIPPED, CANCELLED",
    )

    converted_experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    doe: Mapped[DOE] = relationship("DOE", back_populates="proposed_experiments")

    def __repr__(self) -> str:
        return (
            f"<ProposedExperiment id={self.id!s} run_order={self.run_order} "
            f"condition={self.design_condition_id!r} status={self.status!r}>"
        )


class DOEAnalysis(Base):
    """
    Statistical analysis results for a DOE study.

    Stores Main Effects ($E_A$), Interaction Effects ($E_{AB}$), Response Surface polynomial regression fit,
    ANOVA metrics ($R^2$, Adj $R^2$, RMSE, MAE, sample size $n$), and residual diagnostic plots.
    """

    __tablename__ = "doe_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("does.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doe_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")

    response_property: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_count: Mapped[int] = mapped_column(nullable=False, default=0)

    main_effects: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    interaction_effects: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    regression_model: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    fit_metrics: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    residual_diagnostics: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    doe: Mapped[DOE] = relationship("DOE", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<DOEAnalysis id={self.id!s} doe_id={self.doe_id!s} target={self.response_property!r} n={self.sample_count}>"


# Aliases for Phase 14 naming conventions
DOEStudy = DOE
DOEDesignRun = ProposedExperiment
