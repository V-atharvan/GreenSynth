"""
GreenSynth Analytics — Unit Tests: Model Drift Detector & Performance History Calculator
"""

from __future__ import annotations

import uuid
import pytest

from app.ml.validation.drift_detector import DriftDetector
from app.ml.validation.performance_history import PerformanceHistoryCalculator
from app.models.ml import MLModel
from app.models.validation import ValidationResult


def test_drift_detector():
    detector = DriftDetector()
    baseline_rmse = 0.5

    # Small error case -> No drift
    res1 = detector.check_drift(baseline_rmse, [0.3, 0.4, 0.35, 0.42])
    assert res1.has_drift is False

    # Large error case -> Drift detected (MAE >= 1.5 * baseline_rmse)
    res2 = detector.check_drift(baseline_rmse, [0.85, 0.90, 0.95, 1.10])
    assert res2.has_drift is True
    assert "Potential model drift detected" in res2.warnings[0]


def test_performance_history_calculator():
    calc = PerformanceHistoryCalculator()

    model = MLModel(
        id=uuid.uuid4(),
        training_run_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
        dataset_version="v1",
        name="CuO Model v1",
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
        metrics={"cv_r2": 0.85, "cv_rmse": 0.45},
        library_versions={},
        status="PRODUCTION_CANDIDATE",
    )

    vr1 = ValidationResult(
        id=uuid.uuid4(),
        experiment_id=uuid.uuid4(),
        sample_id=uuid.uuid4(),
        model_id=model.id,
        model_version="1.0",
        target_property="Electrical Conductivity",
        predicted_value=5.2,
        actual_value=5.0,
        unit="S/cm",
        error=-0.2,
        absolute_error=0.2,
        is_within_prediction_interval=True,
        validation_type="PROSPECTIVE",
        validation_status="COMPLETE",
    )

    vr2 = ValidationResult(
        id=uuid.uuid4(),
        experiment_id=uuid.uuid4(),
        sample_id=uuid.uuid4(),
        model_id=model.id,
        model_version="1.0",
        target_property="Electrical Conductivity",
        predicted_value=7.5,
        actual_value=7.1,
        unit="S/cm",
        error=-0.4,
        absolute_error=0.4,
        is_within_prediction_interval=True,
        validation_type="PROSPECTIVE",
        validation_status="COMPLETE",
    )

    history = calc.calculate_history(model, [vr1, vr2])

    assert history.n_experimental_validations == 2
    assert history.experimental_mae == 0.3
    assert history.interval_coverage_rate == 1.0
    assert history.small_sample_warning is True
    assert "small" in history.warnings[0]
