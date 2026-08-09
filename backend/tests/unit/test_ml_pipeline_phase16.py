"""
GreenSynth Analytics — Phase 16 ML Prediction & Model Validation Unit Tests
"""

import pytest
import numpy as np
from app.ml.models.lasso import LassoRegressionModel
from app.ml.prediction.domain_checker import DomainCheckerEngine
from app.ml.validation.readiness_validator import MLReadinessValidator


def test_ml_readiness_validator():
    """Verify MLReadinessValidator returns READY or NOT_READY with reasons."""
    dataset_meta = {"status": "ACTIVE"}
    sample_records = [
        {"temp": 300.0, "cond": 1.2},
        {"temp": 350.0, "cond": 3.4},
        {"temp": 400.0, "cond": 5.8},
        {"temp": 350.0, "cond": 3.2},
        {"temp": 300.0, "cond": 1.5},
    ]
    status, criteria, reasons = MLReadinessValidator.validate_dataset_readiness(
        dataset_meta=dataset_meta,
        sample_records=sample_records,
        target_property="cond",
        feature_names=["temp"],
    )
    assert status in ("READY", "READY_WITH_WARNING")
    assert criteria["dataset_exists"] is True
    assert criteria["target_observed"] is True

    # Test NOT_READY when target missing
    status_fail, _, reasons_fail = MLReadinessValidator.validate_dataset_readiness(
        dataset_meta=dataset_meta,
        sample_records=[{"temp": 300.0, "cond": None}],
        target_property="cond",
        feature_names=["temp"],
    )
    assert status_fail == "NOT_READY"
    assert len(reasons_fail) > 0


def test_lasso_model_fit_and_predict():
    """Verify Lasso regression model fitting, prediction, and feature importance."""
    X = np.array([[300.0], [350.0], [400.0], [450.0]])
    y = np.array([1.2, 3.4, 5.8, 7.2])

    lasso = LassoRegressionModel(hyperparameters={"alpha": 0.1, "random_state": 42})
    lasso.fit(X, y, ["substrate_temperature"])
    assert lasso.is_fitted is True

    y_pred = lasso.predict(np.array([[375.0]]))
    assert len(y_pred) == 1
    assert y_pred[0] > 1.0

    fi = lasso.get_feature_importance(["substrate_temperature"])
    assert "substrate_temperature" in fi
    assert fi["substrate_temperature"] == 1.0


def test_domain_checker_ranges_and_distance():
    """Verify out-of-domain feature range checking and standardized Euclidean distance."""
    input_params = {"temp": 650.0, "spray_rate": 3.0}
    training_ranges = {
        "temp": {"min": 300.0, "max": 400.0},
        "spray_rate": {"min": 2.0, "max": 5.0},
    }
    status, details, warnings = DomainCheckerEngine.evaluate_feature_ranges(input_params, training_ranges)
    assert status == "OUT_OF_DOMAIN"
    assert "temp" in details
    assert details["temp"]["status"] == "OUT_OF_RANGE"
    assert len(warnings) > 0

    # Distance test
    input_v = np.array([650.0, 3.0])
    train_means = np.array([350.0, 3.5])
    train_stds = np.array([40.0, 1.0])
    dist = DomainCheckerEngine.calculate_training_distance(input_v, train_means, train_stds)
    assert dist > 5.0
