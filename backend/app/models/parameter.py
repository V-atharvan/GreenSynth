"""
GreenSynth Analytics — Parameter ORM Models

Defines:
  1. ParameterDefinition: Reusable template for a synthesis parameter per project.
  2. ExperimentParameter: Actual recorded value for a parameter during an experiment.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ParameterDataType(str, enum.Enum):
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"


class ParameterStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ParameterDefinition(Base):
    """
    Project-level parameter definition template.

    Specifies the expected data type, unit, constraints, and whether the parameter
    is required when conducting an experiment in this project.

    Allows projects to be configuration-driven without hard-coding fields in UI or code.
    """

    __tablename__ = "parameter_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parameter_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Human readable name, e.g. Substrate Temperature"
    )
    parameter_code: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Key identifier, e.g. substrate_temperature_c"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ParameterDataType.NUMBER.value
    )
    unit: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="e.g. °C, mL/min, mol/L"
    )
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    minimum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    allowed_values: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="JSON list of allowed values for ENUM type"
    )

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ParameterStatus.ACTIVE.value, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", backref="parameter_definitions"
    )

    def __repr__(self) -> str:
        return (
            f"<ParameterDefinition id={self.id!s} code={self.parameter_code!r} "
            f"type={self.data_type!r} unit={self.unit!r}>"
        )


class ExperimentParameter(Base):
    """
    Actual recorded parameter value used during a specific experiment.

    Preserves the actual value, unit, and link to the parameter definition.
    Histories are immutable — changes to parameter definitions do not overwrite
    historical experiment parameters.
    """

    __tablename__ = "experiment_parameters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parameter_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parameter_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Value storage
    value: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="String representation of actual recorded value"
    )
    value_numeric: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True, comment="Parsed numeric value for database queries"
    )
    unit: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Preserved unit at time of recording"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship(  # type: ignore[name-defined]
        "Experiment", backref="experiment_parameters"
    )
    parameter_definition: Mapped[ParameterDefinition] = relationship(
        "ParameterDefinition"
    )

    def __repr__(self) -> str:
        return (
            f"<ExperimentParameter id={self.id!s} exp={self.experiment_id!s} "
            f"value={self.value!r} unit={self.unit!r}>"
        )
