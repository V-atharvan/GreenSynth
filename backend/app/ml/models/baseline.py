"""
GreenSynth Analytics — Mean Baseline Model

Baseline predictor that always returns the mean of the training target values.
Serves as reference baseline to verify whether ML models genuinely add predictive value.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ml.models.base import BaseMLModel


class MeanBaselineModel(BaseMLModel):
    def __init__(self, hyperparameters: dict[str, Any] | None = None) -> None:
        super().__init__(model_type="MEAN_BASELINE", hyperparameters=hyperparameters)
        self.mean_value: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> MeanBaselineModel:
        if len(y) == 0:
            raise ValueError("Cannot fit MeanBaselineModel on empty data.")
        self.mean_value = float(np.mean(y))
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("MeanBaselineModel is not fitted.")
        n_samples = X.shape[0]
        return np.full((n_samples,), self.mean_value, dtype=float)

    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        return {fname: 0.0 for fname in feature_names}
