"""
GreenSynth Analytics — UV-Vis Scientific Transforms & Tauc Mathematics

Routines:
  1. Wavelength (nm) to Photon Energy E (eV): E = 1239.8419 / wavelength_nm
  2. Absorption Coefficient alpha: alpha = 2.303 * A / thickness
  3. Tauc Variable Y = (y_base * E)^n (n=2 for direct allowed, n=0.5 for indirect allowed)
"""

from __future__ import annotations

import enum
from typing import NamedTuple

import numpy as np

# Planck's constant * speed of light in eV*nm: h*c = 1239.8419 eV*nm
HC_EV_NM = 1239.8419


class TransitionType(str, enum.Enum):
    DIRECT_ALLOWED = "DIRECT_ALLOWED"      # n = 2
    INDIRECT_ALLOWED = "INDIRECT_ALLOWED"  # n = 0.5


TRANSITION_EXPONENTS: dict[TransitionType, float] = {
    TransitionType.DIRECT_ALLOWED: 2.0,
    TransitionType.INDIRECT_ALLOWED: 0.5,
}


class TaucTransformResult(NamedTuple):
    photon_energy_ev: np.ndarray
    tauc_y: np.ndarray
    alpha: np.ndarray | None
    using_alpha: bool
    transition_type: TransitionType
    exponent_n: float
    thickness_cm: float | None
    warning_msg: str | None


def wavelength_to_photon_energy(wavelength_nm: np.ndarray) -> np.ndarray:
    """
    Convert wavelength in nanometers (nm) to photon energy E in electron-volts (eV).

    Formula: E (eV) = 1239.8419 / wavelength_nm
    """
    if np.any(wavelength_nm <= 0):
        raise ValueError("Wavelength values must be positive (> 0 nm).")
    return HC_EV_NM / wavelength_nm


def calculate_absorption_coefficient(
    absorbance: np.ndarray, thickness_cm: float | None
) -> tuple[np.ndarray | None, str | None]:
    """
    Calculate absorption coefficient alpha (cm^-1) from absorbance A.

    Formula: alpha = 2.303 * A / thickness_cm
    Returns (alpha_array, None) if thickness is provided, else (None, warning_message).
    """
    if thickness_cm is None or thickness_cm <= 0:
        return (
            None,
            "Insufficient data for absorption coefficient calculation because sample thickness is missing.",
        )

    # alpha = 2.303 * Absorbance / thickness (cm)
    alpha = 2.302585 * absorbance / thickness_cm
    return alpha, None


def compute_tauc_transform(
    wavelength_nm: np.ndarray,
    absorbance: np.ndarray,
    transition_type: TransitionType = TransitionType.DIRECT_ALLOWED,
    thickness_cm: float | None = None,
) -> TaucTransformResult:
    """
    Compute Tauc plot variables: Photon Energy E (eV) vs (y_base * E)^n.

    If thickness_cm is provided, y_base = alpha (cm^-1).
    Else y_base = Absorbance A (a.u.), with explicit notice logged.
    """
    energy_ev = wavelength_to_photon_energy(wavelength_nm)
    alpha, warning_msg = calculate_absorption_coefficient(absorbance, thickness_cm)

    y_base = alpha if alpha is not None else absorbance
    # Ensure non-negative baseline for exponentiation
    y_base_clean = np.maximum(0.0, y_base)

    exponent = TRANSITION_EXPONENTS.get(transition_type, 2.0)
    tauc_y = (y_base_clean * energy_ev) ** exponent

    return TaucTransformResult(
        photon_energy_ev=energy_ev,
        tauc_y=tauc_y,
        alpha=alpha,
        using_alpha=alpha is not None,
        transition_type=transition_type,
        exponent_n=exponent,
        thickness_cm=thickness_cm,
        warning_msg=warning_msg,
    )
