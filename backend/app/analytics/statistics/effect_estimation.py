"""
GreenSynth Analytics — Effect Estimation & Confidence vs Prediction Intervals Engine (Phase 15)

Provides:
  1. Main & Interaction Effect Size Estimation
  2. 95% Confidence Interval Calculation (Parameter Uncertainty)
  3. 95% Prediction Interval Calculation (Observation Variability)
"""

from __future__ import annotations

import math
import numpy as np
from scipy import stats


class EffectEstimationEngine:
    """Calculates effect sizes, confidence intervals, and prediction intervals."""

    @staticmethod
    def calculate_confidence_and_prediction_intervals(
        y_values: list[float], y_pred: list[float], p_predictors: int = 1, confidence_level: float = 0.95
    ) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
        """
        Distinguishes 95% Confidence Interval (model parameter uncertainty)
        from 95% Prediction Interval (individual observation variability).
        """
        n = len(y_values)
        if n < p_predictors + 2:
            empty_ci = {"lower": [0.0], "upper": [0.0]}
            empty_pi = {"lower": [0.0], "upper": [0.0]}
            return empty_ci, empty_pi

        residuals = np.array(y_values) - np.array(y_pred)
        dof = n - p_predictors - 1
        t_crit = stats.t.ppf((1 + confidence_level) / 2.0, dof)

        mse = np.sum(residuals ** 2) / dof
        se_mean = math.sqrt(mse / n)
        se_pred = math.sqrt(mse * (1.0 + 1.0 / n))

        ci_lower = [round(float(p - t_crit * se_mean), 4) for p in y_pred]
        ci_upper = [round(float(p + t_crit * se_mean), 4) for p in y_pred]

        pi_lower = [round(float(p - t_crit * se_pred), 4) for p in y_pred]
        pi_upper = [round(float(p + t_crit * se_pred), 4) for p in y_pred]

        confidence_interval = {"lower": ci_lower, "upper": ci_upper}
        prediction_interval = {"lower": pi_lower, "upper": pi_upper}

        return confidence_interval, prediction_interval
