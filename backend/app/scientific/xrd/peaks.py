"""
GreenSynth Analytics — XRD Peak Detection Engine

Uses SciPy find_peaks to detect diffraction peaks and computes FWHM (Full Width at Half Maximum)
via linear interpolation across half-maximum intensity boundaries.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.signal import find_peaks, peak_prominences


class DetectedPeakData(NamedTuple):
    two_theta: float
    intensity: float
    fwhm: float | None
    prominence: float | None
    width_degrees: float | None
    index: int


def calculate_peak_fwhm(
    x: np.ndarray, y: np.ndarray, peak_idx: int
) -> float | None:
    """
    Calculate Full Width at Half Maximum (FWHM) in x-units (degrees 2θ) for a peak.

    Finds left and right half-maximum intensity crossing points via linear interpolation.
    """
    peak_y = y[peak_idx]
    if peak_y <= 0:
        return None

    half_y = peak_y / 2.0

    # Find left crossing point
    left_x = x[peak_idx]
    for i in range(peak_idx - 1, -1, -1):
        if y[i] <= half_y:
            # Interpolate between i and i+1
            x1, y1 = x[i], y[i]
            x2, y2 = x[i + 1], y[i + 1]
            if y2 != y1:
                left_x = x1 + (half_y - y1) * (x2 - x1) / (y2 - y1)
            else:
                left_x = x1
            break

    # Find right crossing point
    right_x = x[peak_idx]
    for i in range(peak_idx + 1, len(y)):
        if y[i] <= half_y:
            # Interpolate between i-1 and i
            x1, y1 = x[i - 1], y[i - 1]
            x2, y2 = x[i], y[i]
            if y2 != y1:
                right_x = x1 + (half_y - y1) * (x2 - x1) / (y2 - y1)
            else:
                right_x = x2
            break

    fwhm = float(right_x - left_x)
    return fwhm if fwhm > 0 else None


def detect_xrd_peaks(
    two_theta: np.ndarray,
    intensity: np.ndarray,
    prominence: float | None = None,
    height: float | None = None,
    distance: int | None = 5,
) -> list[DetectedPeakData]:
    """
    Detect XRD diffraction peaks and calculate positions, intensities, and FWHMs.

    Parameters:
      prominence: minimum peak prominence (optional)
      height: minimum peak height (optional)
      distance: minimum index distance between neighboring peaks
    """
    if len(two_theta) < 5 or len(intensity) < 5:
        return []

    # Calculate default prominence if not provided (e.g. 5% of max intensity range)
    y_max = np.max(intensity)
    y_min = np.min(intensity)
    y_range = y_max - y_min

    prom = prominence if prominence is not None else max(1.0, y_range * 0.05)

    peak_indices, _ = find_peaks(
        intensity,
        prominence=prom,
        height=height,
        distance=distance,
    )

    if len(peak_indices) == 0:
        return []

    proms, _, _ = peak_prominences(intensity, peak_indices)

    detected: list[DetectedPeakData] = []
    for i, idx in enumerate(peak_indices):
        p_theta = float(two_theta[idx])
        p_int = float(intensity[idx])
        p_prom = float(proms[i]) if i < len(proms) else None
        fwhm = calculate_peak_fwhm(two_theta, intensity, idx)

        detected.append(
            DetectedPeakData(
                two_theta=p_theta,
                intensity=p_int,
                fwhm=fwhm,
                prominence=p_prom,
                width_degrees=fwhm,
                index=int(idx),
            )
        )

    # Sort peaks by intensity descending
    detected.sort(key=lambda p: p.intensity, reverse=True)
    return detected
