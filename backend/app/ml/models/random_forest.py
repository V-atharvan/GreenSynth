"""
GreenSynth Analytics — Random Forest Regression Model

Random Forest Regressor wrapper.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from app.ml.models.base import BaseMLModel


class RandomForestModel(BaseMLModel):
    def __init__(self, hyperparameters: dict[str, Any] | None = None) -> None:
        super().__init__(model_type="RANDOM_FOREST", hyperparameters=hyperparameters)
        n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        max_depth = self.hyperparameters.get("max_depth")
        if max_depth is not None:
            max_depth = int(max_depth)
        random_state = int(self.hyperparameters.get("random_state", 42))

        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> RandomForestModel:
        if len(y) == 0:
            raise ValueError("Cannot fit RandomForestModel on empty data.")
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("RandomForestModel is not fitted.")
        return self.model.predict(X)

    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        if not self.is_fitted:
            return {fname: 0.0 for fname in feature_names}
        importances = self.model.feature_importances_
        return {fname: float(imp) for fname, imp in zip(feature_names, importances)}
