"""
GreenSynth Analytics — Feature Range Validation & Distance from Training Data Engine (Phase 16)

Evaluates:
  1. Feature Range Check: IN_RANGE, NEAR_BOUNDARY, OUT_OF_RANGE
  2. Standardized Euclidean / Mahalanobis Distance from Training Data
  3. Applicability Status & Extrapolation Warnings
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np


class DomainCheckerEngine:
    """Evaluates whether candidate input parameters fall within training bounds or extrapolate outside."""

    @staticmethod
    def evaluate_feature_ranges(
        input_params: dict[str, float],
        training_ranges: dict[str, dict[str, float]],
    ) -> tuple[str, dict[str, Any], list[str]]:
        """
        Evaluates training range boundaries.

        Returns:
          status: IN_RANGE, NEAR_BOUNDARY, or OUT_OF_RANGE
          details: per-feature status breakdown
          warnings: explicit extrapolation warning messages
        """
        details: dict[str, Any] = {}
        warnings: list[str] = []
        has_out_of_range = False
        has_near_boundary = False

        for f_name, val in input_params.items():
            if val is None or math.isnan(float(val)):
                continue
            v = float(val)
            t_info = training_ranges.get(f_name, {})
            min_v = t_info.get("min", v)
            max_v = t_info.get("max", v)
            f_range = max_v - min_v if max_v > min_v else 1.0

            if v < min_v or v > max_v:
                has_out_of_range = True
                dev = min_v - v if v < min_v else v - max_v
                details[f_name] = {"status": "OUT_OF_RANGE", "val": v, "min": min_v, "max": max_v}
                warnings.append(
                    f"Feature '{f_name}' value ({v}) is outside the experimental training range [{min_v}, {max_v}]."
                )
            elif (v - min_v) / f_range < 0.05 or (max_v - v) / f_range < 0.05:
                has_near_boundary = True
                details[f_name] = {"status": "NEAR_BOUNDARY", "val": v, "min": min_v, "max": max_v}
            else:
                details[f_name] = {"status": "IN_RANGE", "val": v, "min": min_v, "max": max_v}

        if has_out_of_range:
            status = "OUT_OF_DOMAIN"
        elif has_near_boundary:
            status = "CAUTION"
        else:
            status = "VALID"

        return status, details, warnings

    @staticmethod
    def calculate_training_distance(
        input_vector: np.ndarray,
        train_means: np.ndarray,
        train_stds: np.ndarray,
    ) -> float:
        """Calculates standardized Euclidean distance from training centroid."""
        safe_stds = np.where(train_stds > 1e-12, train_stds, 1.0)
        z_scores = (input_vector - train_means) / safe_stds
        distance = float(np.sqrt(np.sum(z_scores ** 2)))
        return round(distance, 4)
