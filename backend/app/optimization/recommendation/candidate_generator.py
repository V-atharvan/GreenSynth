"""
GreenSynth Analytics — Recommendation Candidate Generator

Generates candidate parameter combinations using Grid Search or Reproducible Random Sampling.
Checks existing historical experiments to flag exact or near duplicates.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
import numpy as np

from app.models.ml import MLDatasetRecord


@dataclass
class GeneratedCandidatePoint:
    parameter_set: dict[str, float]
    is_already_tested: bool
    is_near_existing: bool
    nearest_experiment_id: str | None = None
    warning: str | None = None


class CandidateGenerator:
    """
    Generates candidate synthesis parameter sets while avoiding duplicate historical conditions.
    """

    def generate_candidates(
        self,
        parameter_ranges: dict[str, tuple[float, float]],
        training_records: list[MLDatasetRecord],
        n_candidates: int = 50,
        random_seed: int | None = 42,
        near_tolerance_pct: float = 0.05,
    ) -> list[GeneratedCandidatePoint]:
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        # Build list of historical parameter vectors
        param_names = sorted(parameter_ranges.keys())
        hist_points: list[tuple[str, dict[str, float]]] = []

        for r in training_records:
            if r.is_eligible and all(p in r.feature_values for p in param_names):
                hist_points.append((str(r.experiment_id), {p: float(r.feature_values[p]) for p in param_names}))

        raw_candidates: list[dict[str, float]] = []

        # Generate candidates via uniform random sampling across parameter ranges
        for _ in range(n_candidates * 3):
            point = {}
            for pcode, (min_v, max_v) in parameter_ranges.items():
                val = float(np.random.uniform(min_v, max_v))
                point[pcode] = round(val, 2)
            raw_candidates.append(point)

        results: list[GeneratedCandidatePoint] = []
        for cand in raw_candidates:
            is_exact = False
            is_near = False
            nearest_exp_id = None
            warning = None

            for exp_id, h_params in hist_points:
                # Calculate relative distance per parameter
                diffs = []
                for pcode in param_names:
                    min_v, max_v = parameter_ranges[pcode]
                    span = max(max_v - min_v, 1e-5)
                    d = abs(cand[pcode] - h_params[pcode]) / span
                    diffs.append(d)

                max_diff = max(diffs) if diffs else 0.0

                if max_diff < 0.001:
                    is_exact = True
                    nearest_exp_id = exp_id
                    warning = f"Exact duplicate of historical experiment {exp_id}."
                    break
                elif max_diff <= near_tolerance_pct:
                    is_near = True
                    nearest_exp_id = exp_id
                    warning = f"Near existing experiment condition {exp_id} within ±{int(near_tolerance_pct*100)}% tolerance."

            results.append(
                GeneratedCandidatePoint(
                    parameter_set=cand,
                    is_already_tested=is_exact,
                    is_near_existing=is_near,
                    nearest_experiment_id=nearest_exp_id,
                    warning=warning,
                )
            )

        return results
