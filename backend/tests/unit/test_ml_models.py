"""
GreenSynth Analytics — Unit Tests: ML Models (Baseline, Linear, Ridge, RF, GB)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.ml.models.baseline import MeanBaselineModel
from app.ml.models.linear import LinearRegressionModel
from app.ml.models.ridge import RidgeRegressionModel
from app.ml.models.random_forest import RandomForestModel
from app.ml.models.gradient_boosting import GradientBoostingModel


@pytest.fixture
def dummy_data():
    np.random.seed(42)
    X = np.array([
        [250.0, 1.0],
        [300.0, 2.0],
        [350.0, 3.0],
        [400.0, 4.0],
        [450.0, 5.0],
        [500.0, 6.0],
    ])
    y = 0.05 * X[:, 0] + 0.2 * X[:, 1] + 1.0
    feature_names = ["temperature", "spray_rate"]
    return X, y, feature_names


def test_mean_baseline_model(dummy_data):
    X, y, fnames = dummy_data
    model = MeanBaselineModel()
    model.fit(X, y, fnames)

    preds = model.predict(X)
    assert len(preds) == len(y)
    assert np.allclose(preds, np.mean(y))


def test_linear_regression_model(dummy_data):
    X, y, fnames = dummy_data
    model = LinearRegressionModel()
    model.fit(X, y, fnames)

    preds = model.predict(X)
    assert len(preds) == len(y)
    assert np.allclose(preds, y, atol=1e-4)

    importances = model.get_feature_importance(fnames)
    assert "temperature" in importances
    assert "spray_rate" in importances


def test_ridge_model(dummy_data):
    X, y, fnames = dummy_data
    model = RidgeRegressionModel({"alpha": 0.1, "random_state": 42})
    model.fit(X, y, fnames)

    preds = model.predict(X)
    assert len(preds) == len(y)


def test_random_forest_model(dummy_data):
    X, y, fnames = dummy_data
    model = RandomForestModel({"n_estimators": 10, "random_state": 42})
    model.fit(X, y, fnames)

    preds = model.predict(X)
    assert len(preds) == len(y)

    importances = model.get_feature_importance(fnames)
    assert sum(importances.values()) > 0.0


def test_gradient_boosting_model(dummy_data):
    X, y, fnames = dummy_data
    model = GradientBoostingModel({"n_estimators": 10, "learning_rate": 0.1, "random_state": 42})
    model.fit(X, y, fnames)

    preds = model.predict(X)
    assert len(preds) == len(y)


def test_reproducibility(dummy_data):
    X, y, fnames = dummy_data
    m1 = RandomForestModel({"n_estimators": 20, "random_state": 42})
    m1.fit(X, y, fnames)
    p1 = m1.predict(X)

    m2 = RandomForestModel({"n_estimators": 20, "random_state": 42})
    m2.fit(X, y, fnames)
    p2 = m2.predict(X)

    assert np.allclose(p1, p2)
