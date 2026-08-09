"""
GreenSynth Analytics — FTIR Preprocessing Module

Provides Savitzky-Golay noise smoothing and baseline subtraction routines for FTIR spectra.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter


def preprocess_ftir_spectrum(
    wavenumber: np.ndarray,
    signal: np.ndarray,
    smoothing: bool = True,
    savgol_window: int = 11,
    savgol_polyorder: int = 3,
) -> np.ndarray:
    """Apply Savitzky-Golay noise smoothing to FTIR signal if requested."""
    proc_signal = np.copy(signal)

    if smoothing and len(proc_signal) >= savgol_window:
        win = savgol_window if savgol_window % 2 == 1 else savgol_window + 1
        win = min(win, len(proc_signal) if len(proc_signal) % 2 == 1 else len(proc_signal) - 1)
        if win >= 3 and win > savgol_polyorder:
            proc_signal = savgol_filter(proc_signal, window_length=win, polyorder=savgol_polyorder)

    return proc_signal
