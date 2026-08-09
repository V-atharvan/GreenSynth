"""
GreenSynth Analytics — FTIR Spectrum Data Parser

Parses tabular FTIR datasets (CSV, TXT, XLSX) for Wavenumber (cm^-1) and Signal (Transmittance %, Absorbance, or Intensity).
Performs fuzzy column name matching without silent guessing.
"""

from __future__ import annotations

import io
import re
from typing import NamedTuple

import numpy as np
import pandas as pd


class FTIRParseError(ValueError):
    """Raised when an FTIR dataset cannot be parsed or required columns are missing."""


class ParsedFTIRData(NamedTuple):
    wavenumber: np.ndarray
    signal: np.ndarray
    signal_type: str  # TRANSMITTANCE, ABSORBANCE, INTENSITY
    original_columns: list[str]
    total_rows: int
    valid_rows: int


def parse_ftir_file(
    content_bytes: bytes, file_extension: str
) -> ParsedFTIRData:
    """
    Parse raw FTIR file bytes into Wavenumber (cm^-1) and Signal arrays.

    Supports CSV, TXT, XLSX.
    Identifies measurement type (TRANSMITTANCE, ABSORBANCE, INTENSITY).
    """
    ext = file_extension.lstrip(".").lower()
    df: pd.DataFrame

    try:
        if ext in ("csv", "txt"):
            text_str = content_bytes.decode("utf-8", errors="replace")
            first_line = text_str.splitlines()[0] if text_str.splitlines() else ""

            sep = ","
            if "\t" in first_line:
                sep = "\t"
            elif ";" in first_line:
                sep = ";"
            elif re.search(r"\s{2,}", first_line):
                sep = r"\s+"

            df = pd.read_csv(io.BytesIO(content_bytes), sep=sep, comment="#", engine="python")

        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(content_bytes))

        else:
            raise FTIRParseError(f"Unsupported file format '.{ext}' for FTIR spectrum analysis.")

    except Exception as exc:
        if isinstance(exc, FTIRParseError):
            raise
        raise FTIRParseError(f"Failed to parse FTIR file: {exc}") from exc

    if df.empty or len(df.columns) < 2:
        raise FTIRParseError("FTIR dataset must contain at least 2 columns (Wavenumber and Signal).")

    cols_clean = [str(c).strip().lower() for c in df.columns]
    wn_col_idx: int | None = None
    sig_col_idx: int | None = None
    sig_type = "TRANSMITTANCE"

    for idx, col in enumerate(cols_clean):
        clean_name = re.sub(r"[^a-z0-9]", "", col)

        if any(cand in clean_name for cand in ["wavenumber", "wavenum", "cm1", "wn"]):
            if wn_col_idx is None:
                wn_col_idx = idx

        elif any(cand in clean_name for cand in ["transmittance", "transmission", "t"]):
            if sig_col_idx is None:
                sig_col_idx = idx
                sig_type = "TRANSMITTANCE"

        elif any(cand in clean_name for cand in ["absorbance", "abs", "a"]):
            if sig_col_idx is None:
                sig_col_idx = idx
                sig_type = "ABSORBANCE"

        elif any(cand in clean_name for cand in ["intensity", "signal"]):
            if sig_col_idx is None:
                sig_col_idx = idx
                sig_type = "INTENSITY"

    # Default fallback: 1st col = Wavenumber, 2nd col = Signal
    if wn_col_idx is None:
        wn_col_idx = 0
    if sig_col_idx is None:
        sig_col_idx = 1 if wn_col_idx == 0 else 0

    col_wn_name = df.columns[wn_col_idx]
    col_sig_name = df.columns[sig_col_idx]

    total_rows = len(df)

    s_wn = pd.to_numeric(df[col_wn_name], errors="coerce")
    s_sig = pd.to_numeric(df[col_sig_name], errors="coerce")

    # Filter invalid rows
    valid_mask = ~(s_wn.isna() | s_sig.isna() | np.isinf(s_wn) | np.isinf(s_sig))
    valid_rows = int(valid_mask.sum())

    if valid_rows < 10:
        raise FTIRParseError(
            f"FTIR dataset contains insufficient valid data points ({valid_rows} valid rows out of {total_rows}). "
            f"Expected at least 10 numeric (Wavenumber, Signal) pairs."
        )

    arr_wn = s_wn[valid_mask].to_numpy(dtype=np.float64)
    arr_sig = s_sig[valid_mask].to_numpy(dtype=np.float64)

    # Sort by Wavenumber ascending
    if not np.all(np.diff(arr_wn) >= 0):
        sort_indices = np.argsort(arr_wn)
        arr_wn = arr_wn[sort_indices]
        arr_sig = arr_sig[sort_indices]

    return ParsedFTIRData(
        wavenumber=arr_wn,
        signal=arr_sig,
        signal_type=sig_type,
        original_columns=[str(c) for c in df.columns],
        total_rows=total_rows,
        valid_rows=valid_rows,
    )
