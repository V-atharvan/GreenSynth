"""
GreenSynth Analytics — Electrical Unit Conversion Module

Handles explicit unit conversions for electrical quantities:
  - Voltage: V, mV
  - Current: A, mA, uA, nA
  - Resistance: Ohm, kOhm, MOhm
  - Length / Dimensions: m, cm, mm, um
"""

from __future__ import annotations

import enum


class VoltageUnit(str, enum.Enum):
    V = "V"
    MV = "mV"


class CurrentUnit(str, enum.Enum):
    A = "A"
    MA = "mA"
    UA = "uA"
    NA = "nA"


class ResistanceUnit(str, enum.Enum):
    OHM = "Ohm"
    KOHM = "kOhm"
    MOHM = "MOhm"


class LengthUnit(str, enum.Enum):
    M = "m"
    CM = "cm"
    MM = "mm"
    UM = "um"


# Factors to convert to base SI units (Volt, Ampere, Ohm, Meter)
VOLTAGE_TO_VOLTS: dict[VoltageUnit, float] = {
    VoltageUnit.V: 1.0,
    VoltageUnit.MV: 1e-3,
}

CURRENT_TO_AMPERES: dict[CurrentUnit, float] = {
    CurrentUnit.A: 1.0,
    CurrentUnit.MA: 1e-3,
    CurrentUnit.UA: 1e-6,
    CurrentUnit.NA: 1e-9,
}

RESISTANCE_TO_OHMS: dict[ResistanceUnit, float] = {
    ResistanceUnit.OHM: 1.0,
    ResistanceUnit.KOHM: 1e3,
    ResistanceUnit.MOHM: 1e6,
}

LENGTH_TO_CENTIMETERS: dict[LengthUnit, float] = {
    LengthUnit.M: 100.0,
    LengthUnit.CM: 1.0,
    LengthUnit.MM: 0.1,
    LengthUnit.UM: 1e-4,
}

LENGTH_TO_METERS: dict[LengthUnit, float] = {
    LengthUnit.M: 1.0,
    LengthUnit.CM: 1e-2,
    LengthUnit.MM: 1e-3,
    LengthUnit.UM: 1e-6,
}


def convert_voltage_to_volts(val: float, unit: VoltageUnit | str) -> float:
    """Convert voltage value to Volts (V)."""
    u_enum = VoltageUnit(unit)
    return val * VOLTAGE_TO_VOLTS[u_enum]


def convert_current_to_amperes(val: float, unit: CurrentUnit | str) -> float:
    """Convert current value to Amperes (A)."""
    u_enum = CurrentUnit(unit)
    return val * CURRENT_TO_AMPERES[u_enum]


def convert_length_to_cm(val: float, unit: LengthUnit | str) -> float:
    """Convert length value to Centimeters (cm)."""
    u_enum = LengthUnit(unit)
    return val * LENGTH_TO_CENTIMETERS[u_enum]
