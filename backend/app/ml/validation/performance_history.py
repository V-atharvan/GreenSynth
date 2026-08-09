"""
GreenSynth Analytics — Model Performance History Calculator

Aggregates Level 1 Statistical Validation metrics alongside Level 2 & 3 Physical Experimental Validation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np

from app.models.ml import MLModel
from app.models.validation import ValidationResult


@dataclass
class PerformanceHistory:
    model_id: str
    model_name: str
    model_version: str
    target_property: str
    statistical_metrics: dict[str, Any]
    n_experimental_validations: int
    experimental_mae: float | None
    experimental_rmse: float | None
    interval_coverage_rate: float | None
    small_sample_warning: bool
    warnings: list[str] = field(default_factory=list)


class PerformanceHistoryCalculator:
    def calculate_history(
        self, model: MLModel, validation_results: list[ValidationResult]
    ) -> PerformanceHistory:
        warnings: list[str] = []
        n_val = len(validation_results)

        if n_val == 0:
            return PerformanceHistory(
                model_id=str(model.id),
                model_name=model.name,
                model_version=model.version,
                target_property=model.target_property,
                statistical_metrics=model.metrics,
                n_experimental_validations=0,
                experimental_mae=None,
                experimental_rmse=None,
                interval_coverage_rate=None,
                small_sample_warning=True,
                warnings=["Experimental validation sample size is 0. Performance estimates rely solely on cross-validation."],
            )

        abs_errs = [r.absolute_error for r in validation_results]
        sq_errs = [(r.error) ** 2 for r in validation_results]

        mae = float(np.mean(abs_errs))
        rmse = float(np.sqrt(np.mean(sq_errs)))

        # Interval coverage rate
        covered = [r for r in validation_results if r.is_within_prediction_interval is True]
        coverage_rate = float(len(covered) / n_val)

        is_small = n_val < 5
        if is_small:
            warnings.append(
                f"Experimental validation sample size is small (n={n_val}). Performance estimates may be unstable."
            )

        return PerformanceHistory(
            model_id=str(model.id),
            model_name=model.name,
            model_version=model.version,
            target_property=model.target_property,
            statistical_metrics=model.metrics,
            n_experimental_validations=n_val,
            experimental_mae=round(mae, 4),
            experimental_rmse=round(rmse, 4),
            interval_coverage_rate=round(coverage_rate, 4),
            small_sample_warning=is_small,
            warnings=warnings,
        )
