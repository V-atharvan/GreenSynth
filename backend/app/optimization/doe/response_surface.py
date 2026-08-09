"""
GreenSynth Analytics — Response Surface DOE (CCD & Box-Behnken) Matrix Generator
"""

from __future__ import annotations

import itertools
import numpy as np

from app.optimization.doe.schemas import FactorDefinition


def generate_ccd_matrix(factors: list[FactorDefinition], alpha: float = 1.0) -> list[dict[str, float | str]]:
    """
    Generate Central Composite Design (CCD) matrix for continuous factors:
      - 2^k Factorial points (-1, +1)
      - 2k Axial/Star points (-alpha, +alpha)
      - Center points (0, 0)
    """
    k = len(factors)
    if k == 0:
        return []

    # 1. Coded factorial points
    coded_factorial = list(itertools.product([-1.0, 1.0], repeat=k))

    # 2. Coded axial points
    coded_axial = []
    for i in range(k):
        pt_pos = [0.0] * k
        pt_neg = [0.0] * k
        pt_pos[i] = alpha
        pt_neg[i] = -alpha
        coded_axial.append(tuple(pt_pos))
        coded_axial.append(tuple(pt_neg))

    # 3. Center points
    coded_center = [tuple([0.0] * k)]

    all_coded = coded_factorial + coded_axial + coded_center
    design_matrix: list[dict[str, float | str]] = []

    for pt in all_coded:
        row: dict[str, float | str] = {}
        for idx, f in enumerate(factors):
            low = f.lower_bound if f.lower_bound is not None else 0.0
            high = f.upper_bound if f.upper_bound is not None else 1.0
            center = (low + high) / 2.0
            scale = (high - low) / 2.0

            real_val = center + pt[idx] * scale
            row[f.parameter_code] = round(float(real_val), 4)
        design_matrix.append(row)

    return design_matrix


def generate_box_behnken_matrix(factors: list[FactorDefinition]) -> list[dict[str, float | str]]:
    """
    Generate Box-Behnken 3-level Response Surface matrix for k >= 3 continuous factors.
    """
    k = len(factors)
    if k < 3:
        # Fallback to CCD if k < 3
        return generate_ccd_matrix(factors)

    # 3-level coded combinations (-1, 0, 1) where exactly one factor is 0 and others are factorial pairs
    pairs = list(itertools.combinations(range(k), 2))
    coded_points: list[tuple[float, ...]] = []

    for i, j in pairs:
        for val_i in [-1.0, 1.0]:
            for val_j in [-1.0, 1.0]:
                pt = [0.0] * k
                pt[i] = val_i
                pt[j] = val_j
                coded_points.append(tuple(pt))

    # Center points
    coded_points.append(tuple([0.0] * k))

    design_matrix: list[dict[str, float | str]] = []
    for pt in coded_points:
        row: dict[str, float | str] = {}
        for idx, f in enumerate(factors):
            low = f.lower_bound if f.lower_bound is not None else 0.0
            high = f.upper_bound if f.upper_bound is not None else 1.0
            center = (low + high) / 2.0
            scale = (high - low) / 2.0

            real_val = center + pt[idx] * scale
            row[f.parameter_code] = round(float(real_val), 4)
        design_matrix.append(row)

    return design_matrix
