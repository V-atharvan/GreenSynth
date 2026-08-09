"""
GreenSynth Analytics — Parameter Space Distance & Novelty Service

Calculates normalized Euclidean distance in parameter space to historical laboratory experiments.
Detects:
  - ALREADY_TESTED: Identical parameter conditions already executed in lab.
  - SIMILAR_TO_EXISTING_EXPERIMENT / LOW_DISTANCE: Distance <= 0.15.
  - MEDIUM_DISTANCE: Distance between 0.15 and 0.45.
  - HIGH_DISTANCE: Distance > 0.45 (Novel parameter region / exploration candidate).
"""

from __future__ import annotations

import math
from typing import Any


class ParameterDistanceService:
    """
    Parameter space distance & experimental novelty evaluation.
    """

    @staticmethod
    def calculate_distance(
        candidate_params: dict[str, float],
        historical_experiments: list[dict[str, Any]],
        parameter_bounds: dict[str, tuple[float, float]],
    ) -> tuple[str, float, list[str]]:
        """
        Calculate min distance to historical experiments and determine novelty category.

        Returns:
          (novelty_category, min_distance, nearby_experiment_ids)
        """
        if not historical_experiments or not parameter_bounds:
            return "HIGH_DISTANCE", 1.0, []

        min_dist = float("inf")
        nearest_exp_ids: list[str] = []
        is_already_tested = False

        for exp in historical_experiments:
            exp_params = exp.get("parameter_values", {})
            exp_id = str(exp.get("id") or exp.get("experiment_code") or "EXP")

            sq_sum = 0.0
            param_count = 0
            is_identical = True

            for p_code, cand_val in candidate_params.items():
                if p_code in exp_params:
                    min_b, max_b = parameter_bounds.get(p_code, (0.0, 1.0))
                    span = (max_b - min_b) if (max_b and min_b and max_b > min_b) else 1.0

                    hist_val = float(exp_params[p_code])
                    cand_val_f = float(cand_val)

                    diff = abs(cand_val_f - hist_val)
                    if diff > 1e-4:
                        is_identical = False

                    norm_diff = diff / span
                    sq_sum += norm_diff ** 2
                    param_count += 1

            if param_count > 0:
                dist = math.sqrt(sq_sum / param_count)
                if is_identical and param_count == len(candidate_params):
                    is_already_tested = True

                if dist < min_dist:
                    min_dist = dist
                    nearest_exp_ids = [exp_id]
                elif abs(dist - min_dist) < 1e-3:
                    nearest_exp_ids.append(exp_id)

        if min_dist == float("inf"):
            min_dist = 1.0

        if is_already_tested:
            return "ALREADY_TESTED", 0.0, nearest_exp_ids
        elif min_dist <= 0.15:
            return "LOW_DISTANCE", round(min_dist, 4), nearest_exp_ids
        elif min_dist <= 0.45:
            return "MEDIUM_DISTANCE", round(min_dist, 4), nearest_exp_ids
        else:
            return "HIGH_DISTANCE", round(min_dist, 4), nearest_exp_ids
