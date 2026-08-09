"""
GreenSynth Analytics — Scientific Unit Tests: XRD Analysis & Scherrer Calculations
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from app.scientific.xrd.crystallite_size import (
    ScherrerCalculationError,
    calculate_scherrer_crystallite_size,
)
from app.scientific.xrd.parser import XRDParseError, parse_xrd_file
from app.scientific.xrd.peaks import detect_xrd_peaks, calculate_peak_fwhm
from app.scientific.xrd.preprocessing import (
    apply_savitzky_golay_smoothing,
    subtract_rolling_baseline,
)


def test_scherrer_crystallite_size_valid() -> None:
    """
    Test Scherrer equation with known mathematical inputs.

    Inputs:
      2θ = 35.5°  →  θ = 17.75° = 0.309796 rad
      FWHM = 0.4° →  β = 0.4 * (pi/180) = 0.0069813 rad
      λ = 0.15406 nm (Cu-Ka)
      K = 0.9

    Expected D = (0.9 * 0.15406) / (0.0069813 * cos(0.309796))
               = 0.138654 / (0.0069813 * 0.95239)
               = 0.138654 / 0.0066489 = ~20.85 nm
    """
    res = calculate_scherrer_crystallite_size(
        peak_position_2theta_deg=35.5,
        fwhm_deg=0.4,
        wavelength_nm=0.15406,
        shape_factor_k=0.9,
    )
    assert res.crystallite_size_nm == 20.853
    assert res.peak_position_2theta_deg == 35.5
    assert res.fwhm_deg == 0.4
    assert res.wavelength_nm == 0.15406
    assert res.shape_factor_k == 0.9
    assert res.formula == "D = (K * λ) / (β * cos(θ))"


def test_scherrer_missing_fwhm_error() -> None:
    """Rejects non-positive or missing FWHM with ScherrerCalculationError."""
    with pytest.raises(ScherrerCalculationError, match="FWHM is missing or non-positive"):
        calculate_scherrer_crystallite_size(35.5, fwhm_deg=0.0)


def test_scherrer_invalid_wavelength_error() -> None:
    """Rejects invalid non-positive wavelength with ScherrerCalculationError."""
    with pytest.raises(ScherrerCalculationError, match="Invalid X-ray wavelength"):
        calculate_scherrer_crystallite_size(35.5, fwhm_deg=0.4, wavelength_nm=-0.15)


def test_xrd_parser_valid_csv() -> None:
    """Parse valid CSV XRD dataset."""
    csv_bytes = b"2theta,intensity\n20.0,100\n20.1,105\n20.2,110\n20.3,125\n20.4,150\n20.5,200\n20.6,150\n20.7,125\n20.8,110\n20.9,105\n21.0,100\n"
    parsed = parse_xrd_file(csv_bytes, "csv")

    assert parsed.total_rows == 11
    assert parsed.valid_rows == 11
    assert len(parsed.two_theta) == 11
    assert parsed.two_theta[0] == 20.0
    assert parsed.intensity[5] == 200.0


def test_xrd_parser_column_mapping() -> None:
    """Recognize 'angle_2theta' and 'counts' headers."""
    txt_bytes = b"angle_2theta\tcounts\n20.0\t50\n20.5\t60\n21.0\t70\n21.5\t80\n22.0\t90\n22.5\t100\n23.0\t110\n23.5\t120\n24.0\t130\n24.5\t140\n"
    parsed = parse_xrd_file(txt_bytes, "txt")
    assert parsed.valid_rows == 10
    assert parsed.two_theta[-1] == 24.5


def test_xrd_parser_insufficient_data_error() -> None:
    """Dataset with < 10 rows raises XRDParseError."""
    csv_bytes = b"2theta,intensity\n20.0,100\n20.1,105\n"
    with pytest.raises(XRDParseError, match="insufficient valid data points"):
        parse_xrd_file(csv_bytes, "csv")


def test_peak_detection_and_fwhm() -> None:
    """Synthesize a Gaussian peak and verify peak detection and FWHM calculation."""
    theta = np.linspace(30.0, 40.0, 500)
    # Gaussian peak centered at 35.0 deg with FWHM ~ 0.5 deg
    sigma = 0.5 / (2 * math.sqrt(2 * math.log(2)))
    y = 500.0 * np.exp(-((theta - 35.0) ** 2) / (2 * sigma ** 2)) + 50.0

    peaks = detect_xrd_peaks(theta, y, prominence=50.0)

    assert len(peaks) == 1
    p = peaks[0]
    assert abs(p.two_theta - 35.0) < 0.1
    assert abs(p.intensity - 550.0) < 5.0
    assert p.fwhm is not None
    assert abs(p.fwhm - 0.5) < 0.05
