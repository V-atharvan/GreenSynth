"""
GreenSynth Analytics — XRD Preprocessing Engine

Configurable preprocessing routines for XRD patterns:
  - Rolling minimum / polynomial baseline correction
  - Savitzky-Golay noise smoothing
"""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter


def apply_savitzky_golay_smoothing(
    y: np.ndarray, window_length: int = 11, polyorder: int = 3
) -> np.ndarray:
    """
    Apply Savitzky-Golay smoothing filter to intensity array.

    window_length must be an odd positive integer <= len(y).
    """
    if len(y) < 5:
        return y.copy()

    # Ensure window_length is odd and <= len(y)
    wl = min(window_length, len(y))
    if wl % 2 == 0:
        wl -= 1
    if wl <= polyorder:
        wl = polyorder + 2 if (polyorder + 2) % 2 != 0 else polyorder + 3

    if wl > len(y):
        return y.copy()

    return savgol_filter(y, window_length=wl, polyorder=polyorder)


def subtract_rolling_baseline(
    y: np.ndarray, window_size: int = 50
) -> np.ndarray:
    """
    Perform rolling-minimum baseline subtraction.
    """
    if len(y) < window_size:
        min_val = np.min(y)
        return np.maximum(0, y - min_val)

    # Compute rolling minimum baseline
    pad_width = window_size // 2
    padded = np.pad(y, pad_width, mode="edge")
    baseline = np.zeros_like(y)

    for i in range(len(y)):
        baseline[i] = np.min(padded[i : i + window_size])

    corrected = y - baseline
    return np.maximum(0, corrected)
