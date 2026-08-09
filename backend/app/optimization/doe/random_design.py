"""
GreenSynth Analytics — Randomized Candidate DOE Matrix Generator
"""

from __future__ import annotations

import random
from typing import Any

from app.optimization.doe.schemas import FactorDefinition


def generate_random_candidates(
    factors: list[FactorDefinition], requested_runs: int, random_seed: int = 42
) -> list[dict[str, Any]]:
    """
    Generate reproducible random candidate factor conditions within bounds given a random seed.
    """
    rng = random.Random(random_seed)
    candidates: list[dict[str, Any]] = []

    for _ in range(requested_runs):
        row: dict[str, Any] = {}
        for f in factors:
            ftype = f.factor_type.upper()
            if ftype == "CONTINUOUS":
                low = f.lower_bound if f.lower_bound is not None else 0.0
                high = f.upper_bound if f.upper_bound is not None else 1.0
                val = rng.uniform(low, high)
                row[f.parameter_code] = round(val, 4)
            elif ftype == "CATEGORICAL" or ftype == "DISCRETE":
                if isinstance(f.levels, list) and f.levels:
                    row[f.parameter_code] = rng.choice(f.levels)
                else:
                    low = f.lower_bound if f.lower_bound is not None else 0.0
                    high = f.upper_bound if f.upper_bound is not None else 1.0
                    row[f.parameter_code] = round(rng.uniform(low, high), 4)
            else:
                low = f.lower_bound if f.lower_bound is not None else 0.0
                high = f.upper_bound if f.upper_bound is not None else 1.0
                row[f.parameter_code] = round(rng.uniform(low, high), 4)

        candidates.append(row)

    return candidates
