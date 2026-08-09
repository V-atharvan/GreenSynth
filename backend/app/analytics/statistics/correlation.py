"""
GreenSynth Analytics — Correlation Analysis Engine (Pearson & Spearman) (Phase 15 Extended)
"""

from __future__ import annotations

import math
import numpy as np
from scipy import stats

from app.analytics.statistics.schemas import CorrelationMatrixResponse, CorrelationResponse


class CorrelationError(ValueError):
    """Raised when correlation cannot be computed due to insufficient data or mathematical error."""
    pass


def calculate_pearson_correlation(
    x_variable: str,
    y_variable: str,
    x_vals_or_paired: list[float | None] | list[tuple[float | None, float | None]],
    y_vals: list[float | None] | None = None,
) -> CorrelationResponse:
    """Calculate Pearson correlation between two continuous variables with sample size N & warnings."""
    if y_vals is not None:
        paired_values = list(zip(x_vals_or_paired, y_vals))  # type: ignore[arg-type]
    elif x_vals_or_paired and isinstance(x_vals_or_paired[0], (tuple, list)):
        paired_values = x_vals_or_paired  # type: ignore[assignment]
    else:
        paired_values = []

    clean_pairs = [
        (float(x), float(y))
        for x, y in paired_values
        if x is not None and y is not None and not math.isnan(float(x)) and not math.isnan(float(y))
    ]
    n = len(clean_pairs)

    if n < 3:
        raise CorrelationError("Insufficient valid paired data points to compute Pearson correlation.")

    warnings: list[str] = [
        "Correlation indicates statistical association; it does not establish causation."
    ]

    if len(paired_values) - n > 0:
        warnings.append("Correlation may be affected by missing observations.")

    if n < 10:
        warnings.append("Correlation estimate is based on limited observations (N < 10).")

    x_vals_clean = [p[0] for p in clean_pairs]
    y_vals_clean = [p[1] for p in clean_pairs]

    r_val, p_val = stats.pearsonr(x_vals_clean, y_vals_clean)
    r_clean = round(float(r_val), 4)
    p_clean = round(float(p_val), 4)

    if abs(r_clean) >= 0.7:
        strength = "Strong positive linear association" if r_clean >= 0 else "Strong negative linear association"
    elif abs(r_clean) >= 0.4:
        strength = "Moderate positive linear association" if r_clean >= 0 else "Moderate negative linear association"
    else:
        strength = "Weak linear association"

    interp = f"{strength} (r = {r_clean}, p = {p_clean}, N = {n}) between {x_variable} and {y_variable}."

    return CorrelationResponse(
        x_variable=x_variable,
        y_variable=y_variable,
        method="Pearson Correlation",
        pearson_r=r_clean,
        p_value=p_clean,
        sample_size_n=n,
        interpretation=interp,
        warnings=warnings,
    )


def calculate_correlation_matrix(
    variables: list[str],
    data_rows: list[dict[str, float | None]],
    method: str = "PEARSON",
) -> CorrelationMatrixResponse:
    """Calculate multi-variable Pearson or Spearman correlation matrix."""
    matrix: dict[str, dict[str, float]] = {v: {} for v in variables}
    p_matrix: dict[str, dict[str, float]] = {v: {} for v in variables}
    warnings: list[str] = []

    min_n = len(data_rows)
    for v1 in variables:
        for v2 in variables:
            if v1 == v2:
                matrix[v1][v2] = 1.0
                p_matrix[v1][v2] = 0.0
                continue

            paired = [(row.get(v1), row.get(v2)) for row in data_rows]
            clean = [
                (float(x), float(y))
                for x, y in paired
                if x is not None and y is not None and not math.isnan(float(x)) and not math.isnan(float(y))
            ]
            n = len(clean)
            min_n = min(min_n, n)

            if n < 3:
                matrix[v1][v2] = 0.0
                p_matrix[v1][v2] = 1.0
            else:
                x_v = [p[0] for p in clean]
                y_v = [p[1] for p in clean]
                if method.upper() == "SPEARMAN":
                    res = stats.spearmanr(x_v, y_v)
                else:
                    res = stats.pearsonr(x_v, y_v)
                matrix[v1][v2] = round(float(res.statistic), 4)
                p_matrix[v1][v2] = round(float(res.pvalue), 4)

    if min_n < 10:
        warnings.append(f"Correlation estimate is based on limited observations (min N = {min_n}).")

    return CorrelationMatrixResponse(
        method=f"{method.capitalize()} Correlation Matrix",
        variables=variables,
        matrix=matrix,
        p_values=p_matrix,
        sample_size_n=len(data_rows),
        warnings=warnings,
    )
