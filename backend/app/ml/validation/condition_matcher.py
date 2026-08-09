"""
GreenSynth Analytics — Parameter Condition Deviation Matcher (Phase 17)

Evaluates whether laboratory experiments reproduced the predicted synthesis conditions.
"""

from __future__ import annotations

from typing import Any
import math


DEFAULT_TOLERANCES: dict[str, float] = {
    "substrate_temperature": 5.0,  # °C
    "temperature": 5.0,
    "temp": 5.0,
    "spray_rate": 0.2,            # mL/min
    "rate": 0.2,
    "spray_duration": 1.0,        # min
    "duration": 1.0,
    "extract_concentration": 0.5, # % or g/L
    "concentration": 0.1,
    "precursor_concentration": 0.01, # M
}


class ConditionMatcherEngine:
    """Evaluates parameter deviations between predicted and actual laboratory synthesis conditions."""

    @staticmethod
    def evaluate_condition_deviations(
        predicted_params: dict[str, float],
        actual_params: dict[str, float],
        custom_tolerances: dict[str, float] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Calculates parameter deviations between predicted and actual conditions.

        Returns:
            deviations: list of dicts with deviation metadata
            warnings: explicit warning strings for major deviations
        """
        tolerances = DEFAULT_TOLERANCES.copy()
        if custom_tolerances:
            tolerances.update(custom_tolerances)

        deviations: list[dict[str, Any]] = []
        warnings: list[str] = []

        for p_name, p_val in predicted_params.items():
            if p_name not in actual_params:
                continue
            pred_v = float(p_val)
            act_v = float(actual_params[p_name])
            if math.isnan(pred_v) or math.isnan(act_v):
                continue

            abs_dev = round(abs(act_v - pred_v), 4)
            rel_dev = round(abs_dev / abs(pred_v), 4) if abs(pred_v) > 1e-12 else None
            tol = float(tolerances.get(p_name, 1.0))

            if abs_dev <= 1e-6:
                status = "EXACT_MATCH"
            elif abs_dev <= tol:
                status = "MINOR_DEVIATION"
            else:
                status = "MAJOR_DEVIATION"
                warnings.append(
                    f"Parameter '{p_name}' actual value ({act_v}) deviated significantly from predicted ({pred_v}) beyond tolerance (+/-{tol})."
                )

            deviations.append({
                "parameter_name": p_name,
                "predicted_value": pred_v,
                "actual_value": act_v,
                "unit": "unit",
                "absolute_deviation": abs_dev,
                "relative_deviation": rel_dev,
                "tolerance": tol,
                "status": status,
            })

        return deviations, warnings
