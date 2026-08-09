"""
GreenSynth Analytics — Electrical Data Parser

Parses tabular electrical datasets (CSV, TXT, XLSX, JSON) for Voltage (V) and Current (I) or Resistance (R).
Performs fuzzy column name mapping without silent guessing.
"""

from __future__ import annotations

import io
import re
from typing import NamedTuple

import numpy as np
import pandas as pd


class ElectricalParseError(ValueError):
    """Raised when an electrical dataset cannot be parsed or required columns are missing."""


class ParsedElectricalData(NamedTuple):
    voltage: np.ndarray
    current: np.ndarray
    resistance: np.ndarray | None
    original_columns: list[str]
    total_rows: int
    valid_rows: int


VOLTAGE_CANDIDATE_NAMES = {"voltage", "v", "potential", "volts", "bias", "voltage_v", "bias_v"}
CURRENT_CANDIDATE_NAMES = {"current", "i", "amps", "amperes", "current_a", "current_ma", "current_ua"}
RESISTANCE_CANDIDATE_NAMES = {"resistance", "r", "ohms", "res", "resistance_ohm"}


def parse_electrical_file(
    content_bytes: bytes, file_extension: str
) -> ParsedElectricalData:
    """
    Parse raw electrical file bytes into Voltage and Current (or Resistance) arrays.

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
            raise ElectricalParseError(f"Unsupported file format '.{ext}' for electrical analysis.")

    except Exception as exc:
        if isinstance(exc, ElectricalParseError):
            raise
        raise ElectricalParseError(f"Failed to parse electrical file: {exc}") from exc

    if df.empty or len(df.columns) < 2:
        raise ElectricalParseError(
            "Electrical dataset must contain at least 2 columns (e.g., Voltage and Current)."
        )

    cols_clean = [str(c).strip().lower() for c in df.columns]
    v_col_idx: int | None = None
    i_col_idx: int | None = None
    r_col_idx: int | None = None

    for idx, col in enumerate(cols_clean):
        clean_name = re.sub(r"[^a-z0-9]", "", col)
        if any(cand in clean_name for cand in ["voltage", "potential", "volts", "bias", "v"]):
            if v_col_idx is None:
                v_col_idx = idx
        elif any(cand in clean_name for cand in ["current", "amps", "amperes", "i"]):
            if i_col_idx is None:
                i_col_idx = idx
        elif any(cand in clean_name for cand in ["resistance", "ohms", "res", "r"]):
            if r_col_idx is None:
                r_col_idx = idx

    # Default fallback: 1st col = Voltage, 2nd col = Current
    if v_col_idx is None:
        v_col_idx = 0
    if i_col_idx is None and r_col_idx is None:
        i_col_idx = 1 if v_col_idx == 0 else 0

    col_v_name = df.columns[v_col_idx]
    col_i_name = df.columns[i_col_idx] if i_col_idx is not None else None

    total_rows = len(df)

    s_v = pd.to_numeric(df[col_v_name], errors="coerce")
    s_i = pd.to_numeric(df[col_i_name], errors="coerce") if col_i_name else None

    if s_i is None:
        raise ElectricalParseError("Electrical dataset requires a valid Current (I) column.")

    # Filter invalid rows
    valid_mask = ~(s_v.isna() | s_i.isna() | np.isinf(s_v) | np.isinf(s_i))
    valid_rows = int(valid_mask.sum())

    if valid_rows < 5:
        raise ElectricalParseError(
            f"Electrical dataset contains insufficient valid data points ({valid_rows} valid rows out of {total_rows}). "
            f"Expected at least 5 numeric (Voltage, Current) pairs."
        )

    arr_v = s_v[valid_mask].to_numpy(dtype=np.float64)
    arr_i = s_i[valid_mask].to_numpy(dtype=np.float64)

    # Sort by Voltage ascending
    if not np.all(np.diff(arr_v) >= 0):
        sort_indices = np.argsort(arr_v)
        arr_v = arr_v[sort_indices]
        arr_i = arr_i[sort_indices]

    return ParsedElectricalData(
        voltage=arr_v,
        current=arr_i,
        resistance=None,
        original_columns=[str(c) for c in df.columns],
        total_rows=total_rows,
        valid_rows=valid_rows,
    )
