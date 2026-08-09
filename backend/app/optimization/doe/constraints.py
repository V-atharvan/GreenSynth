"""
GreenSynth Analytics — DOE Constraint Evaluator
"""

from __future__ import annotations

import typing
from typing import Any

from app.optimization.doe.schemas import DOEConstraint


def evaluate_candidate_constraints(
    factor_values: dict[str, Any], constraints: list[DOEConstraint] | None
) -> tuple[bool, list[str]]:
    """
    Evaluate candidate factor values against specified constraints.

    Returns (is_valid, list_of_violations).
    """
    if not constraints:
        return True, []

    violations: list[str] = []

    for const in constraints:
        p_code = const.parameter_code
        if p_code not in factor_values:
            continue

        val = factor_values[p_code]
        op = const.operator.upper()
        target = const.value

        try:
            if op == ">=":
                if float(val) < float(target):  # type: ignore[arg-type]
                    violations.append(f"Factor {p_code} value {val} is less than required minimum {target}.")
            elif op == "<=":
                if float(val) > float(target):  # type: ignore[arg-type]
                    violations.append(f"Factor {p_code} value {val} exceeds required maximum {target}.")
            elif op == "=":
                if str(val) != str(target):
                    violations.append(f"Factor {p_code} value {val} does not equal required target {target}.")
            elif op == "BETWEEN":
                if isinstance(target, (list, tuple)) and len(target) == 2:
                    low, high = float(target[0]), float(target[1])
                    if float(val) < low or float(val) > high:
                        violations.append(f"Factor {p_code} value {val} is outside allowed range [{low}, {high}].")
            elif op == "IN":
                if isinstance(target, (list, tuple)):
                    target_strs = [str(t) for t in target]
                    if str(val) not in target_strs:
                        violations.append(f"Factor {p_code} value {val} is not in allowed set {target}.")
        except (ValueError, TypeError) as exc:
            violations.append(f"Constraint evaluation failed for {p_code}: {exc}")

    return len(violations) == 0, violations
