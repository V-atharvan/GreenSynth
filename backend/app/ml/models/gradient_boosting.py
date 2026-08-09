"""
GreenSynth Analytics — Gradient Boosting Model

Gradient Boosting Regressor wrapper.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from app.ml.models.base import BaseMLModel


class GradientBoostingModel(BaseMLModel):
    def __init__(self, hyperparameters: dict[str, Any] | None = None) -> None:
        super().__init__(model_type="GRADIENT_BOOSTING", hyperparameters=hyperparameters)
        n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        learning_rate = float(self.hyperparameters.get("learning_rate", 0.1))
        max_depth = int(self.hyperparameters.get("max_depth", 3))
        random_state = int(self.hyperparameters.get("random_state", 42))

        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> GradientBoostingModel:
        if len(y) == 0:
            raise ValueError("Cannot fit GradientBoostingModel on empty data.")
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("GradientBoostingModel is not fitted.")
        return self.model.predict(X)

    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        if not self.is_fitted:
            return {fname: 0.0 for fname in feature_names}
        importances = self.model.feature_importances_
        return {fname: float(imp) for fname, imp in zip(feature_names, importances)}
