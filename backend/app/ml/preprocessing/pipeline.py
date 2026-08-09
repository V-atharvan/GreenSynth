"""
GreenSynth Analytics — Preprocessing Pipeline

Wraps scikit-learn preprocessing pipelines (StandardScaler or Passthrough)
and records all feature scaling transformation parameters for model reproducibility.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.preprocessing import StandardScaler


class PreprocessingPipeline:
    """
    Manages numerical feature scaling and normalization.
    """

    def __init__(self, scaling: str = "STANDARD") -> None:
        self.scaling = scaling.upper()  # "STANDARD" or "PASSTHROUGH" / "NONE"
        self.scaler: StandardScaler | None = StandardScaler() if self.scaling == "STANDARD" else None
        self.feature_names: list[str] = []
        self.is_fitted: bool = False

    def fit_transform(self, X: np.ndarray, feature_names: list[str]) -> np.ndarray:
        self.feature_names = feature_names
        if self.scaling == "STANDARD" and self.scaler is not None:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X.copy()
        self.is_fitted = True
        return X_scaled

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("PreprocessingPipeline is not fitted yet.")
        if self.scaling == "STANDARD" and self.scaler is not None:
            return self.scaler.transform(X)
        return X.copy()

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"scaling": self.scaling, "feature_names": self.feature_names}
        if self.scaling == "STANDARD" and self.scaler is not None and self.is_fitted:
            config["mean"] = self.scaler.mean_.tolist()
            config["scale"] = self.scaler.scale_.tolist()
            config["var"] = self.scaler.var_.tolist()
        return config

    @staticmethod
    def verify_no_leakage(train_sample_ids: list[Any], test_sample_ids: list[Any]) -> bool:
        """Verifies no overlapping sample IDs between train and test datasets."""
        set_train = set(str(sid) for sid in train_sample_ids)
        set_test = set(str(sid) for sid in test_sample_ids)
        overlap = set_train.intersection(set_test)
        if len(overlap) > 0:
            raise ValueError(f"Data leakage detected! {len(overlap)} sample IDs overlap between Train and Test sets.")
        return True
