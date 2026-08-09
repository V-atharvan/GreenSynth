"""
GreenSynth Analytics — FTIR Peak Detection Engine

Uses SciPy find_peaks to detect absorption bands / transmittance dips in FTIR spectra.
Calculates peak position (Wavenumber cm^-1), signal height, prominence, and width.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.signal import find_peaks, peak_widths


class DetectedFTIRPeak(NamedTuple):
    wavenumber_cm1: float
    signal_value: float
    prominence: float
    width_cm1: float


def detect_ftir_peaks(
    wavenumber: np.ndarray,
    signal: np.ndarray,
    signal_type: str = "TRANSMITTANCE",
    prominence: float | None = None,
    min_distance: int = 10,
) -> list[DetectedFTIRPeak]:
    """
    Detect absorption bands / transmittance minima in FTIR spectrum.

    If signal_type is TRANSMITTANCE, inverts signal so dips become maxima.
    """
    if len(wavenumber) < 10 or len(signal) < 10:
        return []

    # If Transmittance %, absorption bands appear as dips (minima), so invert signal for find_peaks
    fit_sig = -signal if signal_type.upper() == "TRANSMITTANCE" else signal

    # Auto prominence if not supplied (5% of peak-to-peak signal)
    p2p = float(np.max(fit_sig) - np.min(fit_sig))
    prom = prominence if prominence is not None and prominence > 0 else 0.05 * (p2p if p2p > 0 else 1.0)

    peak_indices, properties = find_peaks(
        fit_sig,
        prominence=prom,
        distance=max(1, min_distance),
    )

    if len(peak_indices) == 0:
        return []

    widths, _, _, _ = peak_widths(fit_sig, peak_indices, rel_height=0.5)

    # Convert width from index count to wavenumber delta
    step = float(np.mean(np.diff(wavenumber))) if len(wavenumber) > 1 else 1.0

    peaks: list[DetectedFTIRPeak] = []
    for idx, width_idx in zip(peak_indices, widths):
        peaks.append(
            DetectedFTIRPeak(
                wavenumber_cm1=round(float(wavenumber[idx]), 2),
                signal_value=round(float(signal[idx]), 4),
                prominence=round(float(properties["prominences"][np.where(peak_indices == idx)[0][0]]), 4),
                width_cm1=round(float(width_idx * abs(step)), 2),
            )
        )

    # Sort peaks by prominence descending
    peaks.sort(key=lambda p: p.prominence, reverse=True)
    return peaks
