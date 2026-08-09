"""
GreenSynth Analytics — Scientific Unit Tests: SEM Scale Calibration
"""

from __future__ import annotations

import pytest

from app.scientific.sem.calibration import calculate_physical_distance


def test_sem_scale_calibration_nanometers() -> None:
    """
    Test pixel distance to nm conversion.

    Calibration: 500 nm scale bar = 100 pixels  =>  5 nm/pixel.
    Measurement: 50 pixels => 250 nm.
    """
    res = calculate_physical_distance(
        pixel_distance=50.0,
        scale_bar_nm=500.0,
        scale_bar_pixels=100.0,
    )
    assert res.warning_msg is None
    assert res.physical_distance_nm == 250.0
    assert res.unit == "nm"


def test_sem_scale_calibration_micrometers() -> None:
    """
    Test physical distance >= 1000 nm formatted as micrometers (um).

    Calibration: 2000 nm scale bar = 100 pixels => 20 nm/pixel.
    Measurement: 100 pixels => 2000 nm = 2.0 um.
    """
    res = calculate_physical_distance(
        pixel_distance=100.0,
        scale_bar_nm=2000.0,
        scale_bar_pixels=100.0,
    )
    assert res.warning_msg is None
    assert res.physical_distance_nm == 2.0
    assert res.unit == "um"


def test_sem_missing_scale_warning() -> None:
    """Uncalibrated image scale returns warning notice."""
    res = calculate_physical_distance(
        pixel_distance=50.0,
        scale_bar_nm=None,  # Missing scale bar
        scale_bar_pixels=None,
    )
    assert res.physical_distance_nm is None
    assert res.unit == "px"
    assert "image scale is unavailable" in res.warning_msg  # type: ignore[operator]
