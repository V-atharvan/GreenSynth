"""
GreenSynth Analytics — Parameter Pydantic Schemas

Validation and response schemas for ParameterDefinition and ExperimentParameter.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParameterDataType(StrEnum):
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"


class ParameterStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# ── ParameterDefinition Schemas ─────────────────────────────

class ParameterDefinitionBase(BaseModel):
    parameter_name: str = Field(..., min_length=1, max_length=255, description="Substrate Temperature")
    parameter_code: str = Field(..., min_length=1, max_length=64, description="substrate_temperature_c")
    description: str | None = Field(default=None, max_length=1000)
    data_type: ParameterDataType = ParameterDataType.NUMBER
    unit: str | None = Field(default=None, max_length=64, description="e.g. °C, mL/min")
    required: bool = False
    minimum_value: float | None = None
    maximum_value: float | None = None
    allowed_values: list[str] | None = None
    status: ParameterStatus = ParameterStatus.ACTIVE

    @model_validator(mode="after")
    def validate_range_and_allowed_values(self) -> ParameterDefinitionBase:
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.minimum_value > self.maximum_value
        ):
            raise ValueError(
                f"minimum_value ({self.minimum_value}) cannot be greater than "
                f"maximum_value ({self.maximum_value})."
            )
        if self.data_type == ParameterDataType.ENUM and not self.allowed_values:
            raise ValueError("allowed_values is required when data_type is ENUM.")
        return self


class ParameterDefinitionCreate(ParameterDefinitionBase):
    pass


class ParameterDefinitionUpdate(BaseModel):
    parameter_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    data_type: ParameterDataType | None = None
    unit: str | None = Field(default=None, max_length=64)
    required: bool | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    allowed_values: list[str] | None = None
    status: ParameterStatus | None = None


class ParameterDefinitionResponse(ParameterDefinitionBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── ExperimentParameter Schemas ─────────────────────────────

class ExperimentParameterCreate(BaseModel):
    parameter_definition_id: UUID
    value: str | None = None
    unit: str | None = None
    notes: str | None = None


class ExperimentParameterUpdate(BaseModel):
    value: str | None = None
    unit: str | None = None
    notes: str | None = None


class ExperimentParameterResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    parameter_definition_id: UUID
    value: str | None
    value_numeric: float | None
    unit: str | None
    notes: str | None
    parameter_definition: ParameterDefinitionResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchExperimentParametersInput(BaseModel):
    """Input payload for saving all parameters of an experiment."""

    parameters: list[ExperimentParameterCreate]
