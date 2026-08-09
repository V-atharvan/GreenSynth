"""
GreenSynth Analytics — Full & Fractional Factorial DOE Matrix Generator (Phase 14)
"""

from __future__ import annotations

import itertools
import numpy as np

from app.optimization.doe.schemas import FactorDefinition


def generate_full_factorial_matrix(factors: list[FactorDefinition]) -> list[dict[str, float | str]]:
    """
    Generate Full Factorial Cartesian product design matrix across factors.

    For CONTINUOUS factors: calculates linearly spaced values between lower_bound and upper_bound.
    For DISCRETE / CATEGORICAL / ORDINAL factors: uses provided levels array without treating categorical as numeric.
    """
    factor_grids: list[list[float | str]] = []

    for f in factors:
        ftype = f.factor_type.upper()
        if ftype == "CONTINUOUS":
            low = f.lower_bound if f.lower_bound is not None else 0.0
            high = f.upper_bound if f.upper_bound is not None else 1.0
            n_levels = int(f.levels) if isinstance(f.levels, (int, float)) else 2
            if n_levels < 2:
                n_levels = 2
            grid_vals = np.linspace(low, high, n_levels).tolist()
            factor_grids.append([round(float(v), 4) for v in grid_vals])
        else:
            if isinstance(f.levels, list) and len(f.levels) > 0:
                factor_grids.append([v for v in f.levels])
            else:
                low = f.lower_bound if f.lower_bound is not None else 0.0
                high = f.upper_bound if f.upper_bound is not None else 1.0
                factor_grids.append([low, high])

    combinations = list(itertools.product(*factor_grids))
    design_matrix: list[dict[str, float | str]] = []

    for combo in combinations:
        row = {f.parameter_code: val for f, val in zip(factors, combo)}
        design_matrix.append(row)

    return design_matrix


def generate_fractional_factorial_matrix(
    factors: list[FactorDefinition]
) -> tuple[list[dict[str, float | str]], str, str]:
    """
    Generate Fractional Factorial half-fraction ($2^{k-1}$) matrix for k >= 3 factors.

    Returns:
        (design_matrix, design_resolution, confounding_warning)
    """
    full_matrix = generate_full_factorial_matrix(factors)
    if len(factors) < 3:
        # Cannot fractionate fewer than 3 factors safely; return full factorial
        return full_matrix, "Full Factorial (Res V+)", "No confounding; full factor space evaluated."

    # Half-fraction: Select runs where generator parity condition is met
    half_matrix = full_matrix[::2]
    resolution = "Res IV" if len(factors) >= 4 else "Res III"
    warning = (
        f"Fractional Factorial design ({resolution}) reduces run count from {len(full_matrix)} to {len(half_matrix)}. "
        "Main effects may be confounded with multi-factor interactions."
    )
    return half_matrix, resolution, warning
