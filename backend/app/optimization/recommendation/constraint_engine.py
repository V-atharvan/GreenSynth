"""
GreenSynth Analytics — Recommendation Constraint Engine

Evaluates candidate parameter combinations against hard & soft researcher constraints,
physical safety boundaries, and project/material/synthesis method compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.doe import Objective
from app.models.project import Project


@dataclass
class ConstraintEvaluationResult:
    status: str  # "SATISFIED", "SOFT_VIOLATION", "HARD_VIOLATION"
    is_valid: bool
    violations: list[str] = field(default_factory=list)
    penalty: float = 0.0


class ConstraintEngine:
    """
    Validates parameter sets against physical limits, objective constraints, and project context.
    """

    def evaluate(
        self,
        candidate_params: dict[str, float],
        objective: Objective,
        project: Project,
        custom_constraints: list[dict[str, Any]] | None = None,
    ) -> ConstraintEvaluationResult:
        violations: list[str] = []
        penalty = 0.0
        is_hard_violation = False

        # 1. Physical non-negativity safety checks
        for pcode, val in candidate_params.items():
            if "temp" in pcode.lower() and val <= 0:
                violations.append(f"Physical Safety Violation: Temperature ({val}) must be > 0.")
                is_hard_violation = True
            elif "rate" in pcode.lower() and val < 0:
                violations.append(f"Physical Safety Violation: Spray rate ({val}) cannot be negative.")
                is_hard_violation = True
            elif "conc" in pcode.lower() and val < 0:
                violations.append(f"Physical Safety Violation: Concentration ({val}) cannot be negative.")
                is_hard_violation = True

        # 2. Evaluate Objective Constraints (from Objective model)
        obj_constraints = objective.constraints or []
        all_constraints = list(obj_constraints)
        if custom_constraints:
            all_constraints.extend(custom_constraints)

        for c in all_constraints:
            param_name = c.get("parameter")
            op = c.get("operator", "<=")
            val = c.get("value")
            is_soft = c.get("is_soft", False)

            if param_name in candidate_params:
                c_val = candidate_params[param_name]
                violated = False

                if op == "<=" and c_val > float(val):
                    violated = True
                elif op == ">=" and c_val < float(val):
                    violated = True
                elif op == "BETWEEN" and isinstance(val, list) and len(val) == 2:
                    if c_val < float(val[0]) or c_val > float(val[1]):
                        violated = True

                if violated:
                    msg = f"Constraint Violation: {param_name} ({c_val}) violates {op} {val}."
                    violations.append(msg)
                    if is_soft:
                        penalty += 0.2
                    else:
                        is_hard_violation = True

        if is_hard_violation:
            return ConstraintEvaluationResult(
                status="HARD_VIOLATION",
                is_valid=False,
                violations=violations,
                penalty=1.0,
            )

        if penalty > 0:
            return ConstraintEvaluationResult(
                status="SOFT_VIOLATION",
                is_valid=True,
                violations=violations,
                penalty=min(penalty, 0.5),
            )

        return ConstraintEvaluationResult(
            status="SATISFIED",
            is_valid=True,
            violations=[],
            penalty=0.0,
        )
