"""
GreenSynth Analytics — Prospective & Replicate Validation Engine

Manages prospective experimental validation tracking and replicate statistics aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class ReplicateAggregateResult:
    n_replicates: int
    predicted_value: float
    unit: str
    observed_mean: float
    observed_median: float
    observed_std: float
    observed_cv: float | None
    observed_min: float
    observed_max: float


class ProspectiveValidator:
    """
    Manages prospective validation tracking and aggregate statistics for replicate validation runs.
    """

    def aggregate_replicates(
        self, predicted_value: float, unit: str, actual_values: list[float]
    ) -> ReplicateAggregateResult | None:
        if not actual_values:
            return None

        arr = np.array(actual_values, dtype=float)
        mean_v = float(np.mean(arr))
        median_v = float(np.median(arr))
        std_v = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        cv_v = float(std_v / mean_v) if abs(mean_v) > 1e-7 else None

        return ReplicateAggregateResult(
            n_replicates=len(actual_values),
            predicted_value=predicted_value,
            unit=unit,
            observed_mean=round(mean_v, 4),
            observed_median=round(median_v, 4),
            observed_std=round(std_v, 4),
            observed_cv=round(cv_v, 4) if cv_v is not None else None,
            observed_min=round(float(np.min(arr)), 4),
            observed_max=round(float(np.max(arr)), 4),
        )
