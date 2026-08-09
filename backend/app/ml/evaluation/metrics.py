"""
GreenSynth Analytics — ML Metrics Calculation & Overfitting Detection

Calculates regression performance metrics (MAE, RMSE, R^2, MedAE)
and flags potential overfitting when training R^2 significantly exceeds validation R^2.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, median_absolute_error


@dataclass
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float
    med_ae: float
    n_samples: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "r2": round(self.r2, 4),
            "med_ae": round(self.med_ae, 4),
            "n_samples": self.n_samples,
        }


def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> RegressionMetrics:
    """Calculate standard regression metrics: MAE, RMSE, R^2, MedAE."""
    if len(y_true) == 0:
        return RegressionMetrics(mae=0.0, rmse=0.0, r2=0.0, med_ae=0.0, n_samples=0)

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    
    # R^2 calculation requires at least 2 samples and non-zero variance
    if len(y_true) > 1 and np.var(y_true) > 0:
        r2 = float(r2_score(y_true, y_pred))
    else:
        r2 = 0.0

    med_ae = float(median_absolute_error(y_true, y_pred))

    return RegressionMetrics(
        mae=mae,
        rmse=rmse,
        r2=r2,
        med_ae=med_ae,
        n_samples=len(y_true),
    )


def check_overfitting(train_r2: float, val_r2: float, threshold: float = 0.35) -> bool:
    """
    Flags potential overfitting when training R^2 significantly exceeds validation R^2.
    For example: Train R^2 = 0.98, Val R^2 = 0.42 (gap = 0.56 > 0.35).
    """
    if train_r2 > 0.70 and (train_r2 - val_r2) >= threshold:
        return True
    return False
