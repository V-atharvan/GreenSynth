"""
GreenSynth Analytics — SEM Scale Calibration & Manual Distance Conversion Module

Calculates physical length (nm/um) from pixel distance and scale calibration ratio:
  nm_per_pixel = scale_bar_nm / scale_bar_pixels
  physical_distance_nm = pixel_distance * nm_per_pixel
"""

from __future__ import annotations

from typing import NamedTuple


class PhysicalMeasurementResult(NamedTuple):
    physical_distance_nm: float | None
    unit: str
    warning_msg: str | None


def calculate_physical_distance(
    pixel_distance: float,
    scale_bar_nm: float | None = None,
    scale_bar_pixels: float | None = None,
    nm_per_pixel: float | None = None,
) -> PhysicalMeasurementResult:
    """
    Convert pixel distance to physical distance (nm) using image scale calibration.

    Validation:
      - If scale calibration is missing or uncalibrated, returns warning.
    """
    if pixel_distance <= 0:
        return PhysicalMeasurementResult(
            physical_distance_nm=0.0,
            unit="nm",
            warning_msg="Pixel distance must be greater than zero.",
        )

    calib_ratio = nm_per_pixel
    if calib_ratio is None and scale_bar_nm and scale_bar_pixels and scale_bar_pixels > 0:
        calib_ratio = scale_bar_nm / scale_bar_pixels

    if calib_ratio is None or calib_ratio <= 0:
        return PhysicalMeasurementResult(
            physical_distance_nm=None,
            unit="px",
            warning_msg="Unable to perform physical measurement because image scale is unavailable or uncalibrated.",
        )

    phys_nm = pixel_distance * calib_ratio
    unit = "nm"
    if phys_nm >= 1000.0:
        phys_nm = phys_nm / 1000.0
        unit = "um"

    return PhysicalMeasurementResult(
        physical_distance_nm=round(phys_nm, 2),
        unit=unit,
        warning_msg=None,
    )
