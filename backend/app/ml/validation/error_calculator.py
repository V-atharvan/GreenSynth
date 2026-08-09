"""
GreenSynth Analytics — Validation Error Calculator

Calculates signed error, absolute error, relative error (when denominator is scientifically meaningful),
prediction interval coverage, and evaluates researcher-defined validation criteria.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.models.validation import ValidationCriterion


@dataclass
class ErrorCalculationResult:
    error: float
    absolute_error: float
    relative_error: float | None
    is_within_prediction_interval: bool | None
    criterion_result: str | None  # "SATISFIED", "NOT_SATISFIED", or None
    criterion_details: str | None


def calculate_validation_errors(
    predicted_value: float,
    actual_value: float,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    criterion: ValidationCriterion | None = None,
) -> ErrorCalculationResult:
    """
    Calculate validation errors and evaluate prediction interval and validation criteria.
    """
    err = float(actual_value - predicted_value)
    abs_err = abs(err)

    # Calculate relative error only if denominator |actual_value| > 1e-7
    rel_err: float | None = None
    if abs(actual_value) > 1e-7:
        rel_err = abs_err / abs(actual_value)

    # Check prediction interval coverage
    within_interval: bool | None = None
    if lower_bound is not None and upper_bound is not None:
        within_interval = lower_bound <= actual_value <= upper_bound

    # Evaluate researcher-defined criterion
    criterion_res: str | None = None
    criterion_details: str | None = None

    if criterion is not None:
        val_to_compare: float | None = None

        if criterion.metric == "ABSOLUTE_ERROR":
            val_to_compare = abs_err
        elif criterion.metric == "RELATIVE_ERROR":
            val_to_compare = rel_err
        elif criterion.metric == "WITHIN_INTERVAL":
            if within_interval is True:
                criterion_res = "SATISFIED"
                criterion_details = "Actual result falls within the estimated prediction interval."
            else:
                criterion_res = "NOT_SATISFIED"
                criterion_details = "Actual result falls outside the estimated prediction interval."

        if val_to_compare is not None:
            op = criterion.comparison_operator
            thresh = criterion.threshold
            satisfied = False

            if op == "<=":
                satisfied = val_to_compare <= thresh
            elif op == ">=":
                satisfied = val_to_compare >= thresh
            elif op == "==":
                satisfied = math.isclose(val_to_compare, thresh, abs_tol=1e-5)

            if satisfied:
                criterion_res = "SATISFIED"
                criterion_details = f"Criterion satisfied: {criterion.metric} ({val_to_compare:.4f}) {op} {thresh} {criterion.unit}"
            else:
                criterion_res = "NOT_SATISFIED"
                criterion_details = f"Criterion not satisfied: {criterion.metric} ({val_to_compare:.4f}) is not {op} {thresh} {criterion.unit}"

    return ErrorCalculationResult(
        error=round(err, 4),
        absolute_error=round(abs_err, 4),
        relative_error=round(rel_err, 4) if rel_err is not None else None,
        is_within_prediction_interval=within_interval,
        criterion_result=criterion_res,
        criterion_details=criterion_details,
    )
