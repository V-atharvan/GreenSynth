"""
GreenSynth Analytics — Model Diagnostics Generator

Generates diagnostic plots data:
  - Actual vs. Predicted scatter points
  - Residual distribution (Residual = Actual - Predicted)
  - Feature importances or linear coefficients
"""

from __future__ import annotations

from typing import Any
import numpy as np

from app.ml.models.base import BaseMLModel


def generate_diagnostics(
    model: BaseMLModel,
    X: np.ndarray,
    y_actual: np.ndarray,
    y_pred: np.ndarray,
    feature_names: list[str],
    sample_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate diagnostic data dictionary for frontend plotting."""
    if len(y_actual) == 0:
        return {
            "actual_vs_predicted": [],
            "residuals": [],
            "feature_importance": {},
            "mean_residual": 0.0,
            "residual_std": 0.0,
        }

    residuals = y_actual - y_pred
    mean_residual = float(np.mean(residuals))
    std_residual = float(np.std(residuals))

    actual_vs_pred = []
    residual_list = []

    for idx in range(len(y_actual)):
        s_id = sample_ids[idx] if sample_ids and idx < len(sample_ids) else f"Sample #{idx + 1}"
        act = float(y_actual[idx])
        pred = float(y_pred[idx])
        res = float(residuals[idx])

        actual_vs_pred.append({"sample_id": s_id, "actual": round(act, 4), "predicted": round(pred, 4)})
        residual_list.append({"sample_id": s_id, "actual": round(act, 4), "residual": round(res, 4)})

    importance_dict = model.get_feature_importance(feature_names)

    return {
        "actual_vs_predicted": actual_vs_pred,
        "residuals": residual_list,
        "feature_importance": importance_dict,
        "mean_residual": round(mean_residual, 4),
        "residual_std": round(std_residual, 4),
    }
