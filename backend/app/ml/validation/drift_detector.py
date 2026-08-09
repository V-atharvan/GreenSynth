"""
GreenSynth Analytics — Model Drift Detector

Inspects newly recorded validation errors against model baseline metrics to detect potential model drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class DriftCheckResult:
    has_drift: bool
    drift_score: float
    warnings: list[str] = field(default_factory=list)


class DriftDetector:
    """
    Detects potential model drift by monitoring prospective and holdout validation error trends.
    """

    def check_drift(
        self, baseline_rmse: float, recent_absolute_errors: list[float]
    ) -> DriftCheckResult:
        warnings: list[str] = []
        if len(recent_absolute_errors) < 3:
            return DriftCheckResult(has_drift=False, drift_score=0.0, warnings=[])

        recent_mae = float(np.mean(recent_absolute_errors))
        ratio = recent_mae / max(baseline_rmse, 0.01)

        has_drift = ratio >= 1.5
        if has_drift:
            warnings.append(
                f"Potential model drift detected: Recent prospective validation MAE ({recent_mae:.4f}) "
                f"exceeds training baseline RMSE ({baseline_rmse:.4f}) by {((ratio - 1.0) * 100):.1f}%."
            )

        return DriftCheckResult(
            has_drift=has_drift,
            drift_score=round(ratio, 4),
            warnings=warnings,
        )
