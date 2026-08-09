"""
GreenSynth Analytics — Cross Validation Engine

Performs K-Fold cross validation or GroupKFold cross validation (grouped by experiment_id)
and returns aggregated validation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
from sklearn.model_selection import KFold, GroupKFold

from app.ml.evaluation.metrics import RegressionMetrics, calculate_regression_metrics
from app.ml.preprocessing.pipeline import PreprocessingPipeline
from app.ml.models.base import BaseMLModel


@dataclass
class CVResult:
    cv_folds: int
    mean_mae: float
    mean_rmse: float
    mean_r2: float
    mean_med_ae: float
    fold_metrics: list[dict[str, float | int]]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cv_folds": self.cv_folds,
            "cv_mae": round(self.mean_mae, 4),
            "cv_rmse": round(self.mean_rmse, 4),
            "cv_r2": round(self.mean_r2, 4),
            "cv_med_ae": round(self.mean_med_ae, 4),
            "fold_metrics": self.fold_metrics,
            "warnings": self.warnings,
        }


def run_cross_validation(
    model_factory,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    scaling: str = "STANDARD",
    cv_folds: int = 5,
    groups: list[str] | None = None,
    random_seed: int = 42,
) -> CVResult:
    """
    Executes K-Fold (or GroupKFold if groups are supplied) cross-validation.
    Preprocesses data within each fold to eliminate data leakage across folds.
    """
    n_samples = len(y)
    warnings: list[str] = []

    # Adjust folds if dataset is small
    effective_folds = min(cv_folds, n_samples)
    if effective_folds < 2:
        warnings.append(
            f"Dataset has only {n_samples} observations. Cross-validation requires at least 2 samples."
        )
        return CVResult(
            cv_folds=1,
            mean_mae=0.0,
            mean_rmse=0.0,
            mean_r2=0.0,
            mean_med_ae=0.0,
            fold_metrics=[],
            warnings=warnings,
        )

    if effective_folds < cv_folds:
        warnings.append(
            f"Configured {cv_folds}-fold CV reduced to {effective_folds} folds due to small sample size ({n_samples})."
        )

    # Choose split strategy
    if groups is not None and len(set(groups)) >= 2:
        n_groups = len(set(groups))
        effective_folds = min(effective_folds, n_groups)
        splitter = GroupKFold(n_splits=effective_folds)
        split_iter = splitter.split(X, y, groups=groups)
    else:
        splitter = KFold(n_splits=effective_folds, shuffle=True, random_state=random_seed)
        split_iter = splitter.split(X, y)

    fold_maes: list[float] = []
    fold_rmses: list[float] = []
    fold_r2s: list[float] = []
    fold_med_aes: list[float] = []
    fold_details: list[dict[str, float | int]] = []

    for fold_idx, (train_idx, val_idx) in enumerate(split_iter):
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # 1. Preprocessing within fold
        pipe = PreprocessingPipeline(scaling=scaling)
        X_train_scaled = pipe.fit_transform(X_train, feature_names)
        X_val_scaled = pipe.transform(X_val)

        # 2. Fit model on fold training data
        model: BaseMLModel = model_factory()
        model.fit(X_train_scaled, y_train, feature_names)

        # 3. Predict on fold validation data
        y_val_pred = model.predict(X_val_scaled)

        # 4. Metric calculation
        m = calculate_regression_metrics(y_val, y_val_pred)
        fold_maes.append(m.mae)
        fold_rmses.append(m.rmse)
        fold_r2s.append(m.r2)
        fold_med_aes.append(m.med_ae)

        fold_details.append({
            "fold": fold_idx + 1,
            "train_size": len(train_idx),
            "val_size": len(val_idx),
            "mae": round(m.mae, 4),
            "rmse": round(m.rmse, 4),
            "r2": round(m.r2, 4),
        })

    mean_mae = float(np.mean(fold_maes))
    mean_rmse = float(np.mean(fold_rmses))
    mean_r2 = float(np.mean(fold_r2s))
    mean_med_ae = float(np.mean(fold_med_aes))

    return CVResult(
        cv_folds=effective_folds,
        mean_mae=mean_mae,
        mean_rmse=mean_rmse,
        mean_r2=mean_r2,
        mean_med_ae=mean_med_ae,
        fold_metrics=fold_details,
        warnings=warnings,
    )
