"""
GreenSynth Analytics — Unit Tests: Validation Engine (Errors, Criteria, Unit & Target Matchers, Holdout Leakage)
"""

from __future__ import annotations

import uuid
import pytest

from app.ml.validation.error_calculator import calculate_validation_errors
from app.ml.validation.holdout_validator import HoldoutValidator
from app.ml.validation.target_matcher import TargetMatcher
from app.ml.validation.unit_matcher import UnitMatcher
from app.models.ml import MLDatasetRecord, MLModel
from app.models.validation import ValidationCriterion


def test_error_calculator_basic():
    # Predicted 5.2, Actual 5.0
    res = calculate_validation_errors(predicted_value=5.2, actual_value=5.0)
    assert res.error == -0.2
    assert res.absolute_error == 0.2
    assert res.relative_error == round(0.2 / 5.0, 4)


def test_error_calculator_interval():
    # Prediction: 5.2 [4.6, 5.8], Actual: 5.0 -> Within interval
    res = calculate_validation_errors(
        predicted_value=5.2,
        actual_value=5.0,
        lower_bound=4.6,
        upper_bound=5.8,
    )
    assert res.is_within_prediction_interval is True


def test_error_calculator_criterion():
    criterion = ValidationCriterion(
        property_name="Electrical Conductivity",
        metric="ABSOLUTE_ERROR",
        threshold=0.5,
        unit="S/cm",
        comparison_operator="<=",
    )

    # Satisfied case: abs error 0.2 <= 0.5
    res1 = calculate_validation_errors(predicted_value=5.2, actual_value=5.0, criterion=criterion)
    assert res1.criterion_result == "SATISFIED"
    assert "Criterion satisfied" in res1.criterion_details

    # Not satisfied case: abs error 0.8 > 0.5
    res2 = calculate_validation_errors(predicted_value=5.8, actual_value=5.0, criterion=criterion)
    assert res2.criterion_result == "NOT_SATISFIED"
    assert "Criterion not satisfied" in res2.criterion_details


def test_unit_matcher():
    matcher = UnitMatcher()

    # Same units
    r1 = matcher.normalize(5.2, "S/cm", 5.0, "S/cm")
    assert r1.conversion_applied is False
    assert r1.normalized_predicted == 5.2
    assert r1.normalized_actual == 5.0

    # mS/cm vs S/cm
    r2 = matcher.normalize(5.2, "S/cm", 5200.0, "mS/cm")
    assert r2.conversion_applied is True
    assert r2.normalized_predicted == 5.2
    assert r2.normalized_actual == 5.2


def test_target_matcher():
    matcher = TargetMatcher()

    res1 = matcher.match("Electrical Conductivity", "Electrical Conductivity")
    assert res1.is_match is True

    res2 = matcher.match("Electrical Conductivity", "Electrical Resistivity")
    assert res2.is_match is False
    assert "Mismatch" in res2.warning


def test_holdout_validator_leakage_block():
    validator = HoldoutValidator()

    exp_id_1 = uuid.uuid4()
    exp_id_leak = uuid.uuid4()
    smp_id = uuid.uuid4()

    model = MLModel(
        id=uuid.uuid4(),
        training_run_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
        dataset_version="v1",
        name="Test Model",
        model_type="LINEAR_REGRESSION",
        version="1.0",
        target_property="Electrical Conductivity",
        target_type="CALCULATED",
        target_unit="S/cm",
        feature_names=["temp"],
        feature_specs=[],
        preprocessing_config={},
        hyperparameters={},
        artifact_path="data/models/test/model.joblib",
        metrics={},
        library_versions={},
        status="VALIDATED",
    )

    training_records = [
        MLDatasetRecord(
            id=uuid.uuid4(),
            dataset_id=model.dataset_id,
            experiment_id=exp_id_1,
            sample_id=uuid.uuid4(),
            feature_values={"temp": 300.0},
            target_value=5.0,
            is_eligible=True,
        ),
        MLDatasetRecord(
            id=uuid.uuid4(),
            dataset_id=model.dataset_id,
            experiment_id=exp_id_leak,  # In training set!
            sample_id=uuid.uuid4(),
            feature_values={"temp": 350.0},
            target_value=6.0,
            is_eligible=True,
        ),
    ]

    # Attempt holdout validation on exp_id_leak -> Should FAIL due to LEAKAGE
    res = validator.validate_holdout(
        model=model,
        training_records=training_records,
        holdout_experiment_id=exp_id_leak,
        holdout_sample_id=smp_id,
        predicted_value=6.0,
        predicted_unit="S/cm",
        actual_value=6.1,
        actual_property_name="Electrical Conductivity",
        actual_unit="S/cm",
    )

    assert res.status == "FAILED_LEAKAGE"
    assert "Data Leakage Violation" in res.notes
