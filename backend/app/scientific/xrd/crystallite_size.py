"""
GreenSynth Analytics — XRD Crystallite Size Calculation (Scherrer Equation)

Calculates crystallite size D using the Scherrer equation:
  D = (K * lambda) / (beta * cos(theta))

Unit & Angle Conversions:
  - 2theta in degrees → theta in radians: theta = (2theta / 2) * (pi / 180)
  - FWHM in degrees → beta in radians: beta = fwhm_deg * (pi / 180)
  - lambda in nm (default Cu-Ka1 = 0.15406 nm)
  - Result D in nanometers (nm)
"""

from __future__ import annotations

import math
from typing import NamedTuple


class ScherrerCalculationError(ValueError):
    """Raised when Scherrer calculation inputs are missing or scientifically invalid."""


class ScherrerResult(NamedTuple):
    crystallite_size_nm: float
    peak_position_2theta_deg: float
    fwhm_deg: float
    theta_rad: float
    beta_rad: float
    wavelength_nm: float
    shape_factor_k: float
    formula: str
    assumptions: dict[str, str | float]


# Standard X-ray source wavelengths in nanometers (nm)
XRAY_WAVELENGTHS_NM: dict[str, float] = {
    "Cu_Ka": 0.15406,      # Copper Ka (average)
    "Cu_Ka1": 0.154056,    # Copper Ka1
    "Co_Ka": 0.17889,      # Cobalt Ka
    "Fe_Ka": 0.19360,      # Iron Ka
    "Mo_Ka": 0.07093,      # Molybdenum Ka
}


def calculate_scherrer_crystallite_size(
    peak_position_2theta_deg: float,
    fwhm_deg: float,
    wavelength_nm: float = 0.15406,
    shape_factor_k: float = 0.9,
) -> ScherrerResult:
    """
    Calculate crystallite domain size D (nm) via Scherrer Equation.

    Validation rules:
      - wavelength_nm must be positive (> 0)
      - shape_factor_k must be positive (> 0)
      - fwhm_deg must be positive (> 0)
      - peak_position_2theta_deg must be in range (0°, 180°)
    """
    if wavelength_nm <= 0:
        raise ScherrerCalculationError(
            f"Invalid X-ray wavelength ({wavelength_nm} nm). Wavelength must be positive."
        )

    if shape_factor_k <= 0:
        raise ScherrerCalculationError(
            f"Invalid shape factor K ({shape_factor_k}). Shape factor must be positive."
        )

    if fwhm_deg is None or fwhm_deg <= 0:
        raise ScherrerCalculationError(
            "Cannot calculate crystallite size: FWHM is missing or non-positive."
        )

    if peak_position_2theta_deg <= 0 or peak_position_2theta_deg >= 180:
        raise ScherrerCalculationError(
            f"Invalid peak position (2θ = {peak_position_2theta_deg}°). 2θ must be between 0° and 180°."
        )

    # 1. Convert Bragg angle 2θ (deg) to θ (radians)
    theta_deg = peak_position_2theta_deg / 2.0
    theta_rad = math.radians(theta_deg)

    # 2. Convert FWHM (deg) to β (radians)
    beta_rad = math.radians(fwhm_deg)

    # 3. Compute Scherrer Crystallite Size D = (K * lambda) / (beta * cos(theta))
    cos_theta = math.cos(theta_rad)
    if cos_theta <= 0 or beta_rad <= 0:
        raise ScherrerCalculationError(
            "Mathematical domain error during Scherrer calculation."
        )

    crystallite_size_nm = (shape_factor_k * wavelength_nm) / (beta_rad * cos_theta)

    formula = "D = (K * λ) / (β * cos(θ))"

    assumptions = {
        "formula": formula,
        "shape_factor_K": shape_factor_k,
        "xray_wavelength_lambda_nm": wavelength_nm,
        "peak_position_2theta_deg": peak_position_2theta_deg,
        "bragg_angle_theta_rad": theta_rad,
        "fwhm_deg": fwhm_deg,
        "broadening_beta_rad": beta_rad,
        "broadening_cause": "Pure crystallite size broadening (instrumental broadening not subtracted)",
    }

    return ScherrerResult(
        crystallite_size_nm=round(crystallite_size_nm, 3),
        peak_position_2theta_deg=peak_position_2theta_deg,
        fwhm_deg=fwhm_deg,
        theta_rad=theta_rad,
        beta_rad=beta_rad,
        wavelength_nm=wavelength_nm,
        shape_factor_k=shape_factor_k,
        formula=formula,
        assumptions=assumptions,
    )
