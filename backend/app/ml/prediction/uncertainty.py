"""
GreenSynth Analytics — Prediction Uncertainty Estimator

Provides residual standard deviation interval estimation for model predictions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UncertaintyEstimate:
    predicted_value: float
    uncertainty_lower: float
    uncertainty_upper: float
    uncertainty_margin: float
    method: str


class UncertaintyEstimator:
    """
    Estimates prediction interval [lower, upper] based on model validation residual standard deviation.
    """

    def estimate_uncertainty(
        self,
        predicted_value: float,
        validation_rmse: float,
        confidence_factor: float = 1.96,  # ~95% confidence interval
        method: str = "RESIDUAL_STD_DEV",
    ) -> UncertaintyEstimate:
        margin = confidence_factor * max(validation_rmse, 0.01)
        lower = float(predicted_value - margin)
        upper = float(predicted_value + margin)

        return UncertaintyEstimate(
            predicted_value=float(predicted_value),
            uncertainty_lower=round(lower, 4),
            uncertainty_upper=round(upper, 4),
            uncertainty_margin=round(margin, 4),
            method=method,
        )
