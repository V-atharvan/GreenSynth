"""
GreenSynth Analytics — Lasso Regression Model (Phase 16)
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.linear_model import Lasso

from app.ml.models.base import BaseMLModel


class LassoRegressionModel(BaseMLModel):
    """
    Lasso (L1-regularized) linear regression model wrapper.
    """

    def __init__(self, hyperparameters: dict[str, Any] | None = None) -> None:
        super().__init__(model_type="LASSO", hyperparameters=hyperparameters)
        alpha = float(self.hyperparameters.get("alpha", 1.0))
        random_state = int(self.hyperparameters.get("random_state", 42))
        self.model = Lasso(alpha=alpha, random_state=random_state)

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> LassoRegressionModel:
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        return self.model.predict(X)

    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        if not self.is_fitted:
            return {}
        coefs = self.model.coef_
        total = float(np.sum(np.abs(coefs)))
        if total < 1e-12:
            return {name: round(1.0 / len(feature_names), 4) for name in feature_names}
        return {name: round(float(abs(c) / total), 4) for name, c in zip(feature_names, coefs)}
