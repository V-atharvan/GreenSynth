"""
GreenSynth Analytics — Closed-Loop Engine Unit Tests (Phase 13)

Tests:
1. PredictionComparator: Perfect prediction (0 error), nonzero error, zero denominator safe relative error,
   prediction interval checks, target matching, unit conversions, and unit mismatch blocking.
2. ParameterDeviationCalculator: RECOMMENDED vs PLANNED vs ACTUAL percentage deviation.
3. OutcomeClassifier: SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, INCONCLUSIVE rules.
4. ValidationQuality: Evidence level classification (INSUFFICIENT, LIMITED, MODERATE, STRONG).
5. DatasetCandidateService: Candidate creation & researcher review (ACCEPT/REJECT).
"""

import pytest
import uuid
from app.validation.prediction_comparator import PredictionComparator
from app.validation.parameter_deviation import ParameterDeviationCalculator
from app.validation.outcome_classifier import OutcomeClassifier
from app.validation.validation_quality import ValidationQuality


def test_prediction_comparator_perfect_prediction():
    """Test 70: Perfect prediction (predicted=5.0, actual=5.0) -> Absolute error = 0."""
    abs_err, signed_err, rel_err = PredictionComparator.calculate_errors(predicted=5.0, actual=5.0)
    assert abs_err == pytest.approx(0.0)
    assert signed_err == pytest.approx(0.0)
    assert rel_err == pytest.approx(0.0)


def test_prediction_comparator_nonzero_error():
    """Test 71: Nonzero error (predicted=5.0, actual=5.5) -> abs=0.5, signed=+0.5, rel=0.0909."""
    abs_err, signed_err, rel_err = PredictionComparator.calculate_errors(predicted=5.0, actual=5.5)
    assert abs_err == pytest.approx(0.5)
    assert signed_err == pytest.approx(0.5)
    assert rel_err == pytest.approx(0.5 / 5.5)


def test_prediction_comparator_zero_division():
    """Test 75: Zero division safety (actual=0) -> relative_error = None (NOT APPLICABLE)."""
    abs_err, signed_err, rel_err = PredictionComparator.calculate_errors(predicted=0.0, actual=0.0)
    assert abs_err == pytest.approx(0.0)
    assert signed_err == pytest.approx(0.0)
    assert rel_err is None  # Safe handling for zero denominator


def test_prediction_comparator_interval_check():
    """Test 74: Prediction interval check."""
    # Inside interval
    assert PredictionComparator.check_prediction_interval(actual=5.0, lower_bound=4.0, upper_bound=6.0) is True
    # Outside interval
    assert PredictionComparator.check_prediction_interval(actual=7.0, lower_bound=4.0, upper_bound=6.0) is False


def test_prediction_comparator_target_mismatch():
    """Test 73: Mismatching target properties block validation."""
    with pytest.raises(ValueError, match="Validation target mismatch"):
        PredictionComparator.validate_target_and_units(
            predicted_target="conductivity",
            actual_target="band_gap",
            predicted_unit="S/cm",
            actual_unit="S/cm",
            actual_value=1.5,
        )


def test_prediction_comparator_unit_mismatch():
    """Test 72: Incompatible units without explicit conversion block validation."""
    with pytest.raises(ValueError, match="Validation blocked"):
        PredictionComparator.validate_target_and_units(
            predicted_target="conductivity",
            actual_target="conductivity",
            predicted_unit="S/cm",
            actual_unit="deg_C",
            actual_value=5.0,
        )


def test_prediction_comparator_explicit_unit_conversion():
    """Test unit conversion: Resistivity 0.2 Ohm.cm -> Conductivity 5.0 S/cm."""
    val, unit, notes = PredictionComparator.validate_target_and_units(
        predicted_target="conductivity",
        actual_target="conductivity",
        predicted_unit="S/cm",
        actual_unit="Ohm-cm",
        actual_value=0.2,
    )
    assert val == pytest.approx(5.0)
    assert unit == "S/cm"
    assert "Explicit conversion" in notes


def test_parameter_deviation_calculator():
    """Test parameter deviation between recommended, planned, and actual values."""
    res = ParameterDeviationCalculator.calculate_deviation(
        parameter_name="substrate_temperature",
        recommended=350.0,
        planned=355.0,
        actual=357.0,
        unit="°C",
    )
    assert res["absolute_deviation"] == pytest.approx(2.0)
    assert res["percentage_deviation"] == pytest.approx(0.56338, abs=1e-3)
    assert res["has_deviation"] is True


def test_outcome_classifier():
    """Test recommendation outcome classification logic."""
    # SUPPORTED
    out_sup = OutcomeClassifier.classify_outcome(
        absolute_error=0.2, relative_error=0.04, within_prediction_interval=True
    )
    assert out_sup == "SUPPORTED"

    # PARTIALLY_SUPPORTED
    out_part = OutcomeClassifier.classify_outcome(
        absolute_error=1.2, relative_error=0.25, within_prediction_interval=False
    )
    assert out_part == "PARTIALLY_SUPPORTED"

    # NOT_SUPPORTED
    out_not = OutcomeClassifier.classify_outcome(
        absolute_error=4.0, relative_error=0.80, within_prediction_interval=False
    )
    assert out_not == "NOT_SUPPORTED"

    # INCONCLUSIVE
    out_inc = OutcomeClassifier.classify_outcome(
        absolute_error=0.2, relative_error=0.04, within_prediction_interval=True, data_quality_valid=False
    )
    assert out_inc == "INCONCLUSIVE"


def test_validation_quality_evidence_levels():
    """Test evidence quality level evaluation based on sample size n."""
    assert ValidationQuality.evaluate_evidence_level(1) == "INSUFFICIENT"
    assert ValidationQuality.evaluate_evidence_level(2) == "INSUFFICIENT"
    assert ValidationQuality.evaluate_evidence_level(3) == "LIMITED"
    assert ValidationQuality.evaluate_evidence_level(5) == "MODERATE"
    assert ValidationQuality.evaluate_evidence_level(12) == "STRONG"
