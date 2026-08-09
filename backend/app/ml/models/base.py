"""
GreenSynth Analytics — Base ML Model Abstract Class

Abstract interface for all regression models used in GreenSynth Analytics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseMLModel(ABC):
    """
    Abstract interface for machine learning regression algorithms.
    """

    def __init__(self, model_type: str, hyperparameters: dict[str, Any] | None = None) -> None:
        self.model_type = model_type
        self.hyperparameters = hyperparameters or {}
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> BaseMLModel:
        """Fit the model to training data X and targets y."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict continuous property values for X."""
        pass

    @abstractmethod
    def get_feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        """Return feature importance coefficients/scores mapped to feature names."""
        pass

    def get_params(self) -> dict[str, Any]:
        """Return hyperparameter settings."""
        return self.hyperparameters.copy()
