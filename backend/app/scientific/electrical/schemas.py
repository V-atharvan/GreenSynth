"""
GreenSynth Analytics — Electrical Pydantic Schemas

Input payload & response schemas for electrical measurement processing, I-V curve linear fitting,
sample geometry definition, resistance, resistivity, and conductivity calculations.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.scientific.electrical.geometry import GeometryType
from app.scientific.electrical.units import CurrentUnit, LengthUnit, ResistanceUnit, VoltageUnit


class ElectricalUnitsConfig(BaseModel):
    voltage_unit: VoltageUnit = Field(default=VoltageUnit.V, description="Voltage unit (V, mV)")
    current_unit: CurrentUnit = Field(default=CurrentUnit.A, description="Current unit (A, mA, uA, nA)")
    resistance_unit: ResistanceUnit = Field(default=ResistanceUnit.OHM, description="Resistance unit (Ohm, kOhm, MOhm)")
    length_unit: LengthUnit = Field(default=LengthUnit.CM, description="Length unit (m, cm, mm, um)")


class SampleGeometryConfig(BaseModel):
    geometry_type: GeometryType = Field(default=GeometryType.RECTANGULAR_BAR)
    length: float | None = Field(default=None, gt=0.0, description="Current path length L")
    width: float | None = Field(default=None, gt=0.0, description="Sample width W")
    thickness: float | None = Field(default=None, gt=0.0, description="Sample thickness T")


class ElectricalAnalysisInput(BaseModel):
    units: ElectricalUnitsConfig = Field(default_factory=ElectricalUnitsConfig)
    geometry: SampleGeometryConfig = Field(default_factory=SampleGeometryConfig)
    fit_voltage_min: float | None = Field(default=None, description="Fitting region voltage min")
    fit_voltage_max: float | None = Field(default=None, description="Fitting region voltage max")
    notes: str | None = Field(default=None, max_length=1000)


class IVDataPoint(BaseModel):
    voltage_v: float
    current_a: float


class IVFitLinePoint(BaseModel):
    current_a: float
    fit_voltage_v: float


class ElectricalProcessedResponse(BaseModel):
    analysis_run_id: UUID
    voltage_unit: str
    current_unit: str
    resistance_ohms: float | None = None
    r_squared: float | None = None
    resistivity_ohm_cm: float | None = None
    conductivity_s_cm: float | None = None
    warning_msg: str | None = None
    data_points: list[IVDataPoint]
    fit_line: list[IVFitLinePoint] = Field(default_factory=list)
    total_points: int
