"""
GreenSynth Analytics — Electrical Resistance Engine (I-V Linear Fit)

Calculates Resistance R (Ohms) from I-V curve via linear regression:
  V = R * I + intercept  ->  R = slope = dV/dI
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.stats import linregress


class ResistanceCalculationError(ValueError):
    """Raised when resistance calculation or I-V linear regression fails."""


class ResistanceResult(NamedTuple):
    resistance_ohms: float
    r_squared: float
    slope: float
    intercept: float
    voltage_range_min_v: float
    voltage_range_max_v: float
    points_used: int
    formula: str
    assumptions: dict[str, str | float | int]


def calculate_resistance_from_iv(
    voltage_volts: np.ndarray,
    current_amperes: np.ndarray,
    voltage_min_v: float | None = None,
    voltage_max_v: float | None = None,
) -> ResistanceResult:
    """
    Calculate Electrical Resistance R (Ohms) from I-V curve via linear regression.

    Parameters:
      voltage_volts: array of voltage in Volts (V)
      current_amperes: array of current in Amperes (A)
      voltage_min_v: lower bound of fitting region in V (optional)
      voltage_max_v: upper bound of fitting region in V (optional)
    """
    if len(voltage_volts) < 3 or len(current_amperes) < 3:
        raise ResistanceCalculationError("Insufficient data points for I-V linear regression.")

    vmin = voltage_min_v if voltage_min_v is not None else float(np.min(voltage_volts))
    vmax = voltage_max_v if voltage_max_v is not None else float(np.max(voltage_volts))

    mask = (voltage_volts >= vmin) & (voltage_volts <= vmax)
    points_used = int(np.sum(mask))

    if points_used < 3:
        raise ResistanceCalculationError(
            f"Selected voltage range [{vmin:.2f} V, {vmax:.2f} V] contains "
            f"insufficient valid data points ({points_used} points). Require at least 3 points."
        )

    v_fit = voltage_volts[mask]
    i_fit = current_amperes[mask]

    # Perform SciPy linear regression: V = R * I + c  => slope = R = dV/dI
    reg = linregress(i_fit, v_fit)

    slope = float(reg.slope)  # R in Ohms
    intercept = float(reg.intercept)  # Offset in Volts
    r_squared = float(reg.rvalue ** 2)

    if slope <= 0:
        raise ResistanceCalculationError(
            f"Invalid I-V regression fit: non-positive resistance slope ({slope:.4f} Ohms). "
            f"Check current/voltage sign polarity or fit region."
        )

    resistance_ohms = slope
    formula = "R = dV/dI  [Ohm's Law: V = I*R + c]"

    assumptions = {
        "formula": formula,
        "fitting_range_volts": f"{vmin:.2f} - {vmax:.2f} V",
        "points_in_fit": points_used,
        "regression_r_squared": round(r_squared, 4),
        "fit_slope_ohms": round(resistance_ohms, 4),
        "fit_intercept_volts": round(intercept, 4),
        "interpretation": "Electrical resistance R derived from Ohm's Law linear regression slope of I-V curve.",
    }

    return ResistanceResult(
        resistance_ohms=round(resistance_ohms, 4),
        r_squared=round(r_squared, 4),
        slope=slope,
        intercept=intercept,
        voltage_range_min_v=float(np.min(v_fit)),
        voltage_range_max_v=float(np.max(v_fit)),
        points_used=points_used,
        formula=formula,
        assumptions=assumptions,
    )
