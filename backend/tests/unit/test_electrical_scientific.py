"""
GreenSynth Analytics — Scientific Unit Tests: Electrical & Resistance Engine
"""

from __future__ import annotations

import numpy as np
import pytest

from app.scientific.electrical.geometry import GeometryType, calculate_sample_area_cm2
from app.scientific.electrical.parser import ElectricalParseError, parse_electrical_file
from app.scientific.electrical.resistance import (
    ResistanceCalculationError,
    calculate_resistance_from_iv,
)
from app.scientific.electrical.resistivity import calculate_resistivity_and_conductivity
from app.scientific.electrical.units import (
    CurrentUnit,
    LengthUnit,
    VoltageUnit,
    convert_current_to_amperes,
    convert_length_to_cm,
    convert_voltage_to_volts,
)


def test_electrical_unit_conversions() -> None:
    """Verify unit conversions to Volts, Amperes, and Centimeters."""
    assert convert_voltage_to_volts(500.0, VoltageUnit.MV) == 0.5
    assert convert_voltage_to_volts(5.0, VoltageUnit.V) == 5.0

    assert convert_current_to_amperes(2.0, CurrentUnit.MA) == 0.002
    assert abs(convert_current_to_amperes(50.0, CurrentUnit.UA) - 50e-6) < 1e-9
    assert abs(convert_current_to_amperes(10.0, CurrentUnit.NA) - 10e-9) < 1e-12

    assert convert_length_to_cm(10.0, LengthUnit.MM) == 1.0
    assert convert_length_to_cm(500.0, LengthUnit.UM) == 0.05


def test_electrical_parser_valid_csv() -> None:
    """Parse valid CSV electrical dataset."""
    rows = ["voltage,current"]
    for v in range(-5, 6):
        i = v * 0.01
        rows.append(f"{v},{i}")
    csv_bytes = "\n".join(rows).encode("utf-8")

    parsed = parse_electrical_file(csv_bytes, "csv")
    assert parsed.valid_rows == 11
    assert parsed.voltage[0] == -5.0
    assert parsed.current[-1] == 0.05


def test_electrical_parser_insufficient_data_error() -> None:
    """Dataset with < 5 rows raises ElectricalParseError."""
    csv_bytes = b"voltage,current\n1.0,0.01\n2.0,0.02\n"
    with pytest.raises(ElectricalParseError, match="insufficient valid data points"):
        parse_electrical_file(csv_bytes, "csv")


def test_resistance_linear_regression() -> None:
    """Synthesize I-V curve with R = 100 Ohms and verify linear regression slope."""
    i_amps = np.linspace(-0.05, 0.05, 50)
    # V = R * I + c (R = 100.0 Ohms, c = 0.01 V)
    v_volts = 100.0 * i_amps + 0.01

    res = calculate_resistance_from_iv(v_volts, i_amps)

    assert abs(res.resistance_ohms - 100.0) < 0.01
    assert res.r_squared > 0.999
    assert abs(res.intercept - 0.01) < 0.01
    assert res.formula == "R = dV/dI  [Ohm's Law: V = I*R + c]"


def test_resistance_non_positive_slope_error() -> None:
    """Rejects non-positive I-V slope with ResistanceCalculationError."""
    i_amps = np.linspace(0.01, 0.05, 10)
    v_volts = -50.0 * i_amps  # Negative slope

    with pytest.raises(ResistanceCalculationError, match="non-positive resistance slope"):
        calculate_resistance_from_iv(v_volts, i_amps)


def test_area_and_resistivity_calculation() -> None:
    """
    Test sample cross-sectional area A = W * T, resistivity rho = R * A / L, and conductivity sigma = 1 / rho.

    Inputs:
      R = 100.0 Ohms
      L = 1.0 cm
      W = 0.5 cm
      T = 0.05 cm
      A = 0.5 * 0.05 = 0.025 cm^2
      rho = 100.0 * 0.025 / 1.0 = 2.50 Ohm*cm
      sigma = 1 / 2.50 = 0.40 S/cm
    """
    res = calculate_resistivity_and_conductivity(
        resistance_ohms=100.0,
        geometry_type=GeometryType.RECTANGULAR_BAR,
        length_cm=1.0,
        width_cm=0.5,
        thickness_cm=0.05,
    )

    assert res.warning_msg is None
    assert res.area_cm2 == 0.025
    assert res.resistivity_ohm_cm == 2.5
    assert res.conductivity_s_cm == 0.4


def test_resistivity_missing_thickness_warning() -> None:
    """Missing thickness returns warning and None for resistivity and conductivity."""
    res = calculate_resistivity_and_conductivity(
        resistance_ohms=100.0,
        geometry_type=GeometryType.RECTANGULAR_BAR,
        length_cm=1.0,
        width_cm=0.5,
        thickness_cm=None,  # Missing thickness
    )

    assert res.resistivity_ohm_cm is None
    assert res.conductivity_s_cm is None
    assert "sample thickness (T) is missing" in res.warning_msg  # type: ignore[operator]
