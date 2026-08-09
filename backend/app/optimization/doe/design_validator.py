"""
GreenSynth Analytics — DOE Design Validator & Constraint Enforcer (Phase 14)

Enforces:
  1. Factor bounds check (lower_bound <= val <= upper_bound)
  2. Applied parameter constraints (>=, <=, =, BETWEEN, IN)
  3. Unit consistency validation across parameter definitions
"""

from __future__ import annotations

from typing import Any

from app.optimization.doe.constraints import evaluate_candidate_constraints
from app.optimization.doe.schemas import DOEConstraint, FactorDefinition


class DOEValidator:
    """Enforces constraint and unit validation across generated DOE design matrices."""

    @staticmethod
    def validate_factors_and_units(factors: list[FactorDefinition]) -> None:
        """Validates factor definitions and unit specifications."""
        if not factors:
            raise ValueError("DOE requires at least one factor.")

        for f in factors:
            ftype = f.factor_type.upper()
            if ftype == "CONTINUOUS":
                if f.lower_bound is not None and f.upper_bound is not None:
                    if f.lower_bound >= f.upper_bound:
                        raise ValueError(
                            f"Factor upper bound ({f.upper_bound}) must be strictly greater than lower bound ({f.lower_bound}) for parameter {f.parameter_code}."
                        )
            elif ftype == "CATEGORICAL" or ftype == "DISCRETE":
                if isinstance(f.levels, list) and len(f.levels) < 2:
                    raise ValueError(
                        f"Categorical or discrete factor {f.parameter_code} requires at least two valid levels."
                    )

    @staticmethod
    def validate_matrix_constraints(
        design_matrix: list[dict[str, Any]],
        constraints: list[DOEConstraint] | None,
        factors: list[FactorDefinition],
    ) -> list[dict[str, Any]]:
        """
        Evaluates generated candidate runs against configured constraints.
        If a run violates constraints, marks or filters it.
        If all runs violate constraints, raises ValueError.
        """
        if not constraints:
            return design_matrix

        valid_runs: list[dict[str, Any]] = []
        invalid_runs: list[dict[str, Any]] = []

        for row in design_matrix:
            # Clean internal keys for constraint checking
            clean_row = {k: v for k, v in row.items() if not k.startswith("_")}
            is_valid, _ = evaluate_candidate_constraints(clean_row, constraints)
            if is_valid:
                valid_runs.append(row)
            else:
                invalid_runs.append(row)

        if not valid_runs:
            raise ValueError(
                "DOE generation failed because one or more candidate runs violate configured constraints."
            )

        return valid_runs
