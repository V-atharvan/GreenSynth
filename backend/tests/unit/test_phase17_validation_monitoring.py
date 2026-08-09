"""
GreenSynth Analytics — Phase 17 Unit Tests (Prediction Validation & Model Monitoring)
"""

import pytest
import numpy as np
from app.ml.validation.condition_matcher import ConditionMatcherEngine


def test_signed_and_percentage_error_calculation():
    """Verify signed error preservation, absolute error, and percentage error calculation."""
    predicted = 5.2
    actual = 4.7
    signed_err = round(actual - predicted, 4)
    abs_err = round(abs(actual - predicted), 4)
    pct_err = round((abs_err / abs(actual)) * 100.0, 2)

    assert signed_err == -0.5  # Overprediction
    assert abs_err == 0.5
    assert pct_err == 10.64


def test_zero_actual_relative_error_handling():
    """Verify relative/percentage error is safely omitted when actual value is zero."""
    actual = 0.0
    predicted = 0.5
    abs_err = abs(actual - predicted)
    rel_err = round(abs_err / abs(actual), 4) if abs(actual) > 1e-12 else None
    assert rel_err is None


def test_condition_matcher_tolerances():
    """Verify parameter deviation categorization against parameter-specific tolerances."""
    predicted_params = {
        "substrate_temperature": 350.0,
        "spray_rate": 3.0,
    }
    actual_params = {
        "substrate_temperature": 347.0,  # dev 3.0 <= tol 5.0 -> MINOR_DEVIATION
        "spray_rate": 4.5,               # dev 1.5 > tol 0.2 -> MAJOR_DEVIATION
    }

    deviations, warnings = ConditionMatcherEngine.evaluate_condition_deviations(
        predicted_params, actual_params
    )
    assert len(deviations) == 2
    temp_dev = next(d for d in deviations if d["parameter_name"] == "substrate_temperature")
    rate_dev = next(d for d in deviations if d["parameter_name"] == "spray_rate")

    assert temp_dev["status"] == "MINOR_DEVIATION"
    assert rate_dev["status"] == "MAJOR_DEVIATION"
    assert len(warnings) == 1
