"""
GreenSynth Analytics — Constraint Evaluation Service

Evaluates hard and soft optimization constraints:
  - PARAMETER_RANGE
  - PROPERTY_RANGE
  - FIXED_VALUE
  - CATEGORICAL_ALLOWED_VALUE
  - MODEL_DOMAIN

Status:
  - FEASIBLE: Satisfies all constraints.
  - INFEASIBLE: Violates one or more hard constraints.
  - WARNING: Violates soft constraints.
"""

from __future__ import annotations

from typing import Any


class ConstraintEvaluationService:
    """
    Evaluates candidate parameters and predictions against researcher constraints.
    """

    @staticmethod
    def evaluate_candidate(
        candidate_params: dict[str, float],
        predictions: dict[str, float],
        constraints: list[dict[str, Any]],
    ) -> tuple[str, list[str]]:
        """
        Evaluate feasibility status and collect violation reasons.

        Returns:
          (feasibility_status, violation_reasons)
        """
        if not constraints:
            return "FEASIBLE", []

        reasons: list[str] = []
        has_hard_violation = False
        has_soft_violation = False

        for c in constraints:
            c_type = c.get("constraint_type", "PARAMETER_RANGE")
            target_code = c.get("target_code", "")
            is_hard = c.get("is_hard_constraint", True)

            val: float | None = None
            if c_type in ("PARAMETER_RANGE", "FIXED_VALUE", "CATEGORICAL_ALLOWED_VALUE"):
                val = candidate_params.get(target_code)
            elif c_type == "PROPERTY_RANGE":
                val = predictions.get(target_code)

            if val is None and c_type != "CATEGORICAL_ALLOWED_VALUE":
                continue

            min_v = c.get("minimum_value")
            max_v = c.get("maximum_value")
            fixed_v = c.get("fixed_value")
            allowed_v = c.get("allowed_values")

            violation = False

            if c_type in ("PARAMETER_RANGE", "PROPERTY_RANGE"):
                if min_v is not None and float(val) < float(min_v):
                    violation = True
                    msg = f"'{target_code}' value {val} is below minimum constraint {min_v}."
                elif max_v is not None and float(val) > float(max_v):
                    violation = True
                    msg = f"'{target_code}' value {val} exceeds maximum constraint {max_v}."

            elif c_type == "FIXED_VALUE":
                if fixed_v is not None and abs(float(val) - float(fixed_v)) > 1e-4:
                    violation = True
                    msg = f"'{target_code}' value {val} does not match fixed value constraint {fixed_v}."

            elif c_type == "CATEGORICAL_ALLOWED_VALUE":
                cat_val = str(candidate_params.get(target_code, ""))
                if allowed_v and cat_val not in allowed_v:
                    violation = True
                    msg = f"'{target_code}' value '{cat_val}' is not in allowed list {allowed_v}."

            if violation:
                reasons.append(msg)
                if is_hard:
                    has_hard_violation = True
                else:
                    has_soft_violation = True

        if has_hard_violation:
            return "INFEASIBLE", reasons
        elif has_soft_violation:
            return "WARNING", reasons
        else:
            return "FEASIBLE", []
