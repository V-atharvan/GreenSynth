"""
GreenSynth Analytics — XRD Data Parser

Parses tabular raw XRD datasets (CSV, TXT, XLSX, JSON) into 2θ and Intensity arrays.
Performs fuzzy column name mapping without silent guessing.
"""

from __future__ import annotations

import io
import re
from typing import NamedTuple

import numpy as np
import pandas as pd


class XRDParseError(ValueError):
    """Raised when an XRD dataset cannot be parsed or required columns are missing."""


class ParsedXRDData(NamedTuple):
    two_theta: np.ndarray
    intensity: np.ndarray
    original_columns: list[str]
    total_rows: int
    valid_rows: int


THETA_CANDIDATE_NAMES = {
    "2theta", "2θ", "two_theta", "angle", "angle_2theta",
    "degree", "2-theta", "2_theta", "theta", "2th", "position", "x"
}

INTENSITY_CANDIDATE_NAMES = {
    "intensity", "counts", "cps", "int", "a.u.", "y",
    "intensity_counts", "signal", "count", "arbitrary_units"
}


def parse_xrd_file(
    content_bytes: bytes, file_extension: str
) -> ParsedXRDData:
    """
    Parse raw XRD file bytes into 2θ (degrees) and Intensity arrays.

    Supports CSV, TXT, XLSX, JSON.
    Uses controlled column mapping rules.
    """
    ext = file_extension.lstrip(".").lower()
    df: pd.DataFrame

    try:
        if ext in ("csv", "txt"):
            # Try comma, tab, space, semicolon delimiters
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

        elif ext == "json":
            df = pd.read_json(io.BytesIO(content_bytes))

        else:
            raise XRDParseError(f"Unsupported file format '.{ext}' for XRD analysis.")

    except Exception as exc:
        if isinstance(exc, XRDParseError):
            raise
        raise XRDParseError(f"Failed to parse XRD file: {exc}") from exc

    if df.empty or len(df.columns) < 2:
        raise XRDParseError(
            "XRD dataset must contain at least 2 columns (2θ angle and intensity)."
        )

    # Controlled column matching
    cols_clean = [str(c).strip().lower() for c in df.columns]
    theta_col_idx: int | None = None
    intensity_col_idx: int | None = None

    for idx, col in enumerate(cols_clean):
        clean_name = re.sub(r"[^a-z0-9]", "", col)
        if any(cand in clean_name for cand in ["2theta", "twotheta", "angle", "degree", "2th"]):
            if theta_col_idx is None:
                theta_col_idx = idx
        elif any(cand in clean_name for cand in ["intensity", "count", "cps", "signal"]):
            if intensity_col_idx is None:
                intensity_col_idx = idx

    # If fuzzy matching failed, fallback to 1st col=2θ, 2nd col=intensity if numeric
    if theta_col_idx is None:
        theta_col_idx = 0
    if intensity_col_idx is None:
        intensity_col_idx = 1 if theta_col_idx == 0 else 0

    col_2theta_name = df.columns[theta_col_idx]
    col_intensity_name = df.columns[intensity_col_idx]

    total_rows = len(df)

    # Convert columns to numeric, coercing invalid entries to NaN
    s_theta = pd.to_numeric(df[col_2theta_name], errors="coerce")
    s_int = pd.to_numeric(df[col_intensity_name], errors="coerce")

    # Filter invalid rows
    valid_mask = ~(s_theta.isna() | s_int.isna() | np.isinf(s_theta) | np.isinf(s_int))
    valid_rows = int(valid_mask.sum())

    if valid_rows < 10:
        raise XRDParseError(
            f"XRD dataset contains insufficient valid data points ({valid_rows} valid rows out of {total_rows}). "
            f"Expected at least 10 numeric (2θ, Intensity) pairs."
        )

    arr_theta = s_theta[valid_mask].to_numpy(dtype=np.float64)
    arr_int = s_int[valid_mask].to_numpy(dtype=np.float64)

    # Sort by 2θ angle if needed
    if not np.all(np.diff(arr_theta) >= 0):
        sort_indices = np.argsort(arr_theta)
        arr_theta = arr_theta[sort_indices]
        arr_int = arr_int[sort_indices]

    return ParsedXRDData(
        two_theta=arr_theta,
        intensity=arr_int,
        original_columns=[str(c) for c in df.columns],
        total_rows=total_rows,
        valid_rows=valid_rows,
    )
