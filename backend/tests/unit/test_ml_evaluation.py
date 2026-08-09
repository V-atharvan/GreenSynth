"""
GreenSynth Analytics — Unit Tests: ML Evaluation & Cross Validation
"""

from __future__ import annotations

import numpy as np
import pytest

from app.ml.evaluation.metrics import calculate_regression_metrics, check_overfitting
from app.ml.evaluation.cross_validation import run_cross_validation
from app.ml.models.linear import LinearRegressionModel
from app.ml.models.random_forest import RandomForestModel


def test_regression_metrics():
    y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    y_pred = np.array([11.0, 19.0, 31.0, 39.0, 51.0])

    m = calculate_regression_metrics(y_true, y_pred)
    assert m.mae == 1.0
    assert m.rmse == 1.0
    assert m.r2 > 0.95
    assert m.n_samples == 5


def test_overfitting_check():
    # Overfit case: High train R2, low val R2
    assert check_overfitting(train_r2=0.98, val_r2=0.40) is True

    # Good generalization case
    assert check_overfitting(train_r2=0.88, val_r2=0.85) is False


def test_cross_validation():
    X = np.array([
        [250.0, 1.0],
        [300.0, 2.0],
        [350.0, 3.0],
        [400.0, 4.0],
        [450.0, 5.0],
        [500.0, 6.0],
    ])
    y = np.array([10.0, 15.0, 20.0, 25.0, 30.0, 35.0])
    fnames = ["temp", "spray"]

    cv_res = run_cross_validation(
        model_factory=lambda: LinearRegressionModel({"fit_intercept": True}),
        X=X,
        y=y,
        feature_names=fnames,
        scaling="STANDARD",
        cv_folds=3,
        random_seed=42,
    )

    assert cv_res.cv_folds == 3
    assert cv_res.mean_mae >= 0.0
    assert cv_res.mean_r2 <= 1.0
    assert len(cv_res.fold_metrics) == 3
