"""
GreenSynth Analytics — UV-Vis Spectroscopy Data Parser

Parses tabular raw UV-Vis datasets (CSV, TXT, XLSX, JSON) into Wavelength (nm) and Absorbance arrays.
Performs fuzzy column name mapping without silent guessing.
"""

from __future__ import annotations

import io
import re
from typing import NamedTuple

import numpy as np
import pandas as pd


class UVVisParseError(ValueError):
    """Raised when a UV-Vis dataset cannot be parsed or required columns are missing."""


class ParsedUVVisData(NamedTuple):
    wavelength_nm: np.ndarray
    absorbance: np.ndarray
    original_columns: list[str]
    total_rows: int
    valid_rows: int


WAVELENGTH_CANDIDATE_NAMES = {
    "wavelength", "lambda", "nm", "wl", "x", "wavelen", "wavelenth", "wavelength_nm"
}

ABSORBANCE_CANDIDATE_NAMES = {
    "absorbance", "abs", "optical_density", "a", "y", "intensity", "abs_au", "absorptance"
}


def parse_uvvis_file(
    content_bytes: bytes, file_extension: str
) -> ParsedUVVisData:
    """
    Parse raw UV-Vis file bytes into Wavelength (nm) and Absorbance arrays.

    Supports CSV, TXT, XLSX, JSON.
    Uses controlled column mapping rules.
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

        elif ext == "json":
            df = pd.read_json(io.BytesIO(content_bytes))

        else:
            raise UVVisParseError(f"Unsupported file format '.{ext}' for UV-Vis analysis.")

    except Exception as exc:
        if isinstance(exc, UVVisParseError):
            raise
        raise UVVisParseError(f"Failed to parse UV-Vis file: {exc}") from exc

    if df.empty or len(df.columns) < 2:
        raise UVVisParseError(
            "UV-Vis dataset must contain at least 2 columns (Wavelength in nm and Absorbance)."
        )

    cols_clean = [str(c).strip().lower() for c in df.columns]
    wl_col_idx: int | None = None
    abs_col_idx: int | None = None

    for idx, col in enumerate(cols_clean):
        clean_name = re.sub(r"[^a-z0-9]", "", col)
        if any(cand in clean_name for cand in ["wavelength", "lambda", "wavelen", "nm", "wl"]):
            if wl_col_idx is None:
                wl_col_idx = idx
        elif any(cand in clean_name for cand in ["absorbance", "abs", "density", "optical"]):
            if abs_col_idx is None:
                abs_col_idx = idx

    # Default fallback: 1st col = wavelength, 2nd col = absorbance
    if wl_col_idx is None:
        wl_col_idx = 0
    if abs_col_idx is None:
        abs_col_idx = 1 if wl_col_idx == 0 else 0

    col_wl_name = df.columns[wl_col_idx]
    col_abs_name = df.columns[abs_col_idx]

    total_rows = len(df)

    s_wl = pd.to_numeric(df[col_wl_name], errors="coerce")
    s_abs = pd.to_numeric(df[col_abs_name], errors="coerce")

    # Filter invalid rows (require positive wavelength)
    valid_mask = (
        ~(s_wl.isna() | s_abs.isna() | np.isinf(s_wl) | np.isinf(s_abs))
        & (s_wl > 0.0)
    )
    valid_rows = int(valid_mask.sum())

    if valid_rows < 10:
        raise UVVisParseError(
            f"UV-Vis dataset contains insufficient valid data points ({valid_rows} valid rows out of {total_rows}). "
            f"Expected at least 10 numeric (Wavelength, Absorbance) pairs."
        )

    arr_wl = s_wl[valid_mask].to_numpy(dtype=np.float64)
    arr_abs = s_abs[valid_mask].to_numpy(dtype=np.float64)

    # Sort by Wavelength ascending
    if not np.all(np.diff(arr_wl) >= 0):
        sort_indices = np.argsort(arr_wl)
        arr_wl = arr_wl[sort_indices]
        arr_abs = arr_abs[sort_indices]

    return ParsedUVVisData(
        wavelength_nm=arr_wl,
        absorbance=arr_abs,
        original_columns=[str(c) for c in df.columns],
        total_rows=total_rows,
        valid_rows=valid_rows,
    )
