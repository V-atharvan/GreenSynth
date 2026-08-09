"""
GreenSynth Analytics — Domain Checking Service for Candidate Conditions

Classifies candidate parameter conditions relative to the model's training data domain:
  - IN_DOMAIN: All input features lie within the [min, max] training bounds.
  - NEAR_BOUNDARY: Input features lie within 5% of training boundaries.
  - OUT_OF_DOMAIN: One or more input features exceed the training data range.
"""

from __future__ import annotations

from typing import Any


class DomainCheckService:
    """
    Domain suitability evaluation.
    """

    @staticmethod
    def evaluate_candidate_domain(
        candidate_params: dict[str, float],
        training_feature_bounds: dict[str, tuple[float, float]],
    ) -> tuple[str, list[str]]:
        """
        Evaluate domain status for a candidate parameter set.
        """
        if not training_feature_bounds:
            return "IN_DOMAIN", []

        warnings: list[str] = []
        is_out = False
        is_near = False

        for param_code, val in candidate_params.items():
            if param_code not in training_feature_bounds:
                continue

            min_b, max_b = training_feature_bounds[param_code]
            if min_b is None or max_b is None:
                continue

            val_f = float(val)
            span = max_b - min_b if max_b > min_b else 1.0

            if val_f < min_b or val_f > max_b:
                is_out = True
                warnings.append(
                    f"Parameter '{param_code}' value {val_f} lies OUT_OF_DOMAIN (training range: [{min_b}, {max_b}])."
                )
            else:
                # Check 5% boundary zone
                lower_margin = min_b + 0.05 * span
                upper_margin = max_b - 0.05 * span
                if val_f <= lower_margin or val_f >= upper_margin:
                    is_near = True

        if is_out:
            return "OUT_OF_DOMAIN", warnings
        elif is_near:
            return "NEAR_BOUNDARY", ["Candidate conditions are near the training data boundary."]
        else:
            return "IN_DOMAIN", []
