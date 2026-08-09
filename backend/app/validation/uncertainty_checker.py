"""
GreenSynth Analytics — Uncertainty Checker

Strictly separates model prediction uncertainty from physical laboratory measurement uncertainty.
"""

from typing import Dict, Any, Optional


class UncertaintyChecker:
    """
    Keeps model prediction uncertainty (sigma_pred) and measurement uncertainty (sigma_meas) separate.
    """

    @staticmethod
    def format_uncertainty_breakdown(
        predicted_value: float,
        prediction_lower: Optional[float],
        prediction_upper: Optional[float],
        actual_value: float,
        measurement_uncertainty: Optional[float],
    ) -> Dict[str, Any]:
        """
        Formats dual uncertainty reporting without merging them automatically.
        """
        pred_uncertainty_str = "N/A"
        if prediction_lower is not None and prediction_upper is not None:
            half_width = (prediction_upper - prediction_lower) / 2.0
            pred_uncertainty_str = f"± {half_width:.4f} (95% CI: [{prediction_lower:.4f}, {prediction_upper:.4f}])"

        meas_uncertainty_str = f"± {measurement_uncertainty:.4f}" if measurement_uncertainty is not None else "Not specified"

        # Check if actual interval overlaps prediction interval
        overlap = None
        if prediction_lower is not None and prediction_upper is not None and measurement_uncertainty is not None:
            actual_min = actual_value - measurement_uncertainty
            actual_max = actual_value + measurement_uncertainty
            overlap = not (actual_max < prediction_lower or actual_min > prediction_upper)

        return {
            "prediction_uncertainty": pred_uncertainty_str,
            "measurement_uncertainty": meas_uncertainty_str,
            "uncertainty_intervals_overlap": overlap,
            "note": "Model prediction uncertainty and physical measurement uncertainty are evaluated independently.",
        }
