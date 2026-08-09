"""
GreenSynth Analytics — Scientific Unit Tests: UV-Vis & Tauc Optical Band Gap Engine
"""

from __future__ import annotations

import numpy as np
import pytest

from app.scientific.uvvis.band_gap import (
    BandGapCalculationError,
    calculate_optical_band_gap,
)
from app.scientific.uvvis.parser import UVVisParseError, parse_uvvis_file
from app.scientific.uvvis.transforms import (
    TransitionType,
    calculate_absorption_coefficient,
    compute_tauc_transform,
    wavelength_to_photon_energy,
)


def test_wavelength_to_photon_energy() -> None:
    """Verify E (eV) = 1239.8419 / wavelength (nm)."""
    wl = np.array([400.0, 500.0, 620.0])
    energy = wavelength_to_photon_energy(wl)

    assert abs(energy[0] - 3.0996) < 0.01
    assert abs(energy[1] - 2.4797) < 0.01
    assert abs(energy[2] - 1.9997) < 0.01

    with pytest.raises(ValueError, match="Wavelength values must be positive"):
        wavelength_to_photon_energy(np.array([-10.0, 500.0]))


def test_absorption_coefficient_calculation() -> None:
    """Verify alpha = 2.303 * A / thickness_cm and missing thickness warning."""
    abs_arr = np.array([0.5, 1.0, 1.5])

    # Case A: Thickness provided (0.1 cm)
    alpha, warning = calculate_absorption_coefficient(abs_arr, thickness_cm=0.1)
    assert warning is None
    assert alpha is not None
    assert abs(alpha[1] - 23.02585) < 0.01

    # Case B: Thickness missing
    alpha_none, warning_msg = calculate_absorption_coefficient(abs_arr, thickness_cm=None)
    assert alpha_none is None
    assert "sample thickness is missing" in warning_msg  # type: ignore[operator]


def test_uvvis_parser_valid_csv() -> None:
    """Parse valid CSV UV-Vis dataset."""
    rows = ["wavelength,absorbance"]
    for wl in range(300, 800, 10):
        rows.append(f"{wl},{0.5 + 0.001*wl}")
    csv_bytes = "\n".join(rows).encode("utf-8")

    parsed = parse_uvvis_file(csv_bytes, "csv")
    assert parsed.valid_rows == 50
    assert parsed.wavelength_nm[0] == 300.0
    assert abs(parsed.absorbance[-1] - 1.29) < 0.01


def test_uvvis_parser_insufficient_data_error() -> None:
    """Dataset with < 10 rows raises UVVisParseError."""
    csv_bytes = b"wavelength,absorbance\n400,0.5\n410,0.6\n"
    with pytest.raises(UVVisParseError, match="insufficient valid data points"):
        parse_uvvis_file(csv_bytes, "csv")


def test_tauc_linear_regression_band_gap() -> None:
    """Synthesize a direct semiconductor absorption edge (Eg = 2.10 eV) and test Tauc band gap fit."""
    energy_ev = np.linspace(1.5, 3.5, 100)
    # Tauc Direct (y = (A*E)^2 = 100 * (E - 2.10) for E >= 2.10 else 0)
    tauc_y = np.maximum(0.0, 100.0 * (energy_ev - 2.10))

    res = calculate_optical_band_gap(
        energy_ev,
        tauc_y,
        energy_min_ev=2.2,
        energy_max_ev=3.4,
    )

    assert abs(res.band_gap_ev - 2.10) < 0.02
    assert res.r_squared > 0.99
    assert res.points_used > 50


def test_band_gap_missing_points_error() -> None:
    """Fitting energy range with < 3 points raises BandGapCalculationError."""
    energy_ev = np.linspace(1.5, 3.5, 100)
    tauc_y = np.maximum(0.0, 100.0 * (energy_ev - 2.10))

    with pytest.raises(BandGapCalculationError, match="contains insufficient valid data points"):
        calculate_optical_band_gap(energy_ev, tauc_y, energy_min_ev=3.48, energy_max_ev=3.50)
