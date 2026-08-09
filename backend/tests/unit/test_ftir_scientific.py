"""
GreenSynth Analytics — Scientific Unit Tests: FTIR Engine & Peak Detection
"""

from __future__ import annotations

import numpy as np
import pytest

from app.scientific.ftir.parser import FTIRParseError, parse_ftir_file
from app.scientific.ftir.peaks import detect_ftir_peaks
from app.scientific.ftir.preprocessing import preprocess_ftir_spectrum


def test_ftir_parser_valid_csv() -> None:
    """Parse valid CSV FTIR dataset."""
    rows = ["wavenumber,transmittance"]
    for wn in range(400, 4000, 20):
        # Dip at ~1700 cm^-1 (C=O stretch)
        t_val = 95.0 - 50.0 * np.exp(-((wn - 1700) ** 2) / (2 * (30 ** 2)))
        rows.append(f"{wn},{t_val:.2f}")
    csv_bytes = "\n".join(rows).encode("utf-8")

    parsed = parse_ftir_file(csv_bytes, "csv")
    assert parsed.valid_rows == 180
    assert parsed.signal_type == "TRANSMITTANCE"
    assert parsed.wavenumber[0] == 400.0


def test_ftir_parser_insufficient_data_error() -> None:
    """Dataset with < 10 rows raises FTIRParseError."""
    csv_bytes = b"wavenumber,transmittance\n1000,90\n1100,85\n"
    with pytest.raises(FTIRParseError, match="insufficient valid data points"):
        parse_ftir_file(csv_bytes, "csv")


def test_ftir_savitzky_golay_smoothing() -> None:
    """Test Savitzky-Golay noise smoothing on FTIR spectrum."""
    wn = np.linspace(400, 4000, 200)
    clean_sig = 90.0 - 40.0 * np.exp(-((wn - 1700) ** 2) / 1000)
    noisy_sig = clean_sig + np.random.normal(0, 1.5, size=200)

    smoothed = preprocess_ftir_spectrum(wn, noisy_sig, smoothing=True, savgol_window=11)
    assert len(smoothed) == len(noisy_sig)
    # Variance of smoothed signal should be lower than noisy signal
    assert np.var(np.diff(smoothed)) < np.var(np.diff(noisy_sig))


def test_ftir_peak_detection() -> None:
    """Detect synthetic absorption dip at 1700 cm^-1 in transmittance spectrum."""
    wn = np.linspace(400, 4000, 500)
    # Transmittance dip at 1700 cm^-1
    t_sig = 95.0 - 50.0 * np.exp(-((wn - 1700) ** 2) / (2 * (25 ** 2)))

    peaks = detect_ftir_peaks(wn, t_sig, signal_type="TRANSMITTANCE", prominence=5.0)
    assert len(peaks) >= 1
    main_peak = peaks[0]
    assert abs(main_peak.wavenumber_cm1 - 1700.0) < 15.0
    assert main_peak.signal_value < 50.0
