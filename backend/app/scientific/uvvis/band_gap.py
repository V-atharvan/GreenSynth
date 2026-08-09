"""
GreenSynth Analytics — Optical Band Gap Calculation (Tauc Linear Regression)

Performs linear regression on selected Tauc plot region:
  y = slope * E + intercept
Optical Band Gap Eg is derived as the x-intercept (where y = 0):
  Eg = -intercept / slope
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.stats import linregress


class BandGapCalculationError(ValueError):
    """Raised when linear regression or band gap calculation fails."""


class BandGapResult(NamedTuple):
    band_gap_ev: float
    r_squared: float
    slope: float
    intercept: float
    energy_range_min: float
    energy_range_max: float
    points_used: int
    formula: str
    assumptions: dict[str, str | float | int]


def calculate_optical_band_gap(
    photon_energy_ev: np.ndarray,
    tauc_y: np.ndarray,
    energy_min_ev: float | None = None,
    energy_max_ev: float | None = None,
) -> BandGapResult:
    """
    Calculate Optical Band Gap Eg (eV) via Tauc Plot Linear Regression.

    Parameters:
      energy_min_ev: lower bound of fitting region in eV (optional)
      energy_max_ev: upper bound of fitting region in eV (optional)
    """
    if len(photon_energy_ev) < 5 or len(tauc_y) < 5:
        raise BandGapCalculationError("Insufficient data points for Tauc linear regression.")

    # Determine mask for selected energy fitting region
    emin = energy_min_ev if energy_min_ev is not None else float(np.min(photon_energy_ev))
    emax = energy_max_ev if energy_max_ev is not None else float(np.max(photon_energy_ev))

    mask = (photon_energy_ev >= emin) & (photon_energy_ev <= emax)
    points_used = int(np.sum(mask))

    if points_used < 3:
        raise BandGapCalculationError(
            f"Selected energy range [{emin:.2f} eV, {emax:.2f} eV] contains "
            f"insufficient valid data points ({points_used} points). Require at least 3 points."
        )

    x_fit = photon_energy_ev[mask]
    y_fit = tauc_y[mask]

    # Perform SciPy linear regression
    reg = linregress(x_fit, y_fit)

    slope = float(reg.slope)
    intercept = float(reg.intercept)
    r_squared = float(reg.rvalue ** 2)

    if slope <= 0:
        raise BandGapCalculationError(
            f"Invalid Tauc regression fit: non-positive slope ({slope:.4f}). "
            f"Please adjust the fitting region energy range."
        )

    # Derive x-intercept Eg = -intercept / slope
    band_gap_ev = -intercept / slope

    if band_gap_ev <= 0 or band_gap_ev > 10.0:
        raise BandGapCalculationError(
            f"Calculated optical band gap ({band_gap_ev:.2f} eV) is outside expected semiconductor range (0 to 10 eV)."
        )

    formula = "Eg = -intercept / slope  [from (alpha*h*nu)^n = A*(h*nu - Eg)]"

    assumptions = {
        "formula": formula,
        "fitting_range_ev": f"{emin:.2f} - {emax:.2f} eV",
        "points_in_fit": points_used,
        "regression_r_squared": round(r_squared, 4),
        "fit_slope": round(slope, 4),
        "fit_intercept": round(intercept, 4),
        "interpretation": "Optical band gap derived from linear extrapolation of Tauc absorption edge.",
    }

    return BandGapResult(
        band_gap_ev=round(band_gap_ev, 3),
        r_squared=round(r_squared, 4),
        slope=slope,
        intercept=intercept,
        energy_range_min=float(np.min(x_fit)),
        energy_range_max=float(np.max(x_fit)),
        points_used=points_used,
        formula=formula,
        assumptions=assumptions,
    )
