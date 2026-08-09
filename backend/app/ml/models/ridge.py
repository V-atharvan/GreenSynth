"""
GreenSynth Analytics — Ridge Regression Model

L2-regularized linear regression model wrapper.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.linear_model import Ridge

from app.ml.models.base import BaseMLModel


class RidgeRegressionModel(BaseMLModel):
    def __init__(self, hyperparameters: dict[str, Any] | None = None) -> None:
        super().__init__(model_type="RIDGE", hyperparameters=hyperparameters)
        alpha = float(self.hyperparameters.get("alpha", 1.0))
        random_state = self.hyperparameters.get("random_state", 42)
        self.model = Ridge(alpha=alpha, random_state=random_state)

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> RidgeRegressionModel:
        if len(y) == 0:
            raise ValueError("Cannot fit RidgeRegressionModel on empty data.")
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("RidgeRegressionModel is not fitted.")
        return self.model.predict(X)

    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        if not self.is_fitted:
            return {fname: 0.0 for fname in feature_names}
        coefs = self.model.coef_
        if len(coefs.shape) > 1:
            coefs = coefs.ravel()
        return {fname: float(c) for fname, c in zip(feature_names, coefs)}
