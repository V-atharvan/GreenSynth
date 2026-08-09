"""
GreenSynth Analytics — ML Dataset Validator

Provides data quality inspection, minimum sample size validation, target variance checking,
and explicit indicators for scientific dataset readiness.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Any

from app.ml.dataset.builder import DatasetBuildResult


@dataclass
class DatasetQualityIndicators:
    total_records: int
    eligible_records: int
    excluded_records: int
    missing_values_count: int
    duplicate_records_count: int
    potential_outliers_count: int
    target_mean: float | None
    target_std: float | None
    target_min: float | None
    target_max: float | None
    feature_ranges: dict[str, dict[str, float]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    is_valid_for_training: bool = True


class DatasetValidator:
    """
    Validates an assembled ML dataset prior to model training.
    Does NOT produce a single meaningless score; provides explicit indicators and warnings.
    """

    MIN_OBSERVATIONS_WARNING: int = 5

    def validate(self, build_result: DatasetBuildResult) -> DatasetQualityIndicators:
        eligible = [r for r in build_result.records if r.is_eligible and r.target_value is not None]
        eligible_count = len(eligible)
        excluded_count = build_result.excluded_count

        warnings: list[str] = []
        is_valid = True

        if eligible_count == 0:
            warnings.append("Insufficient data: 0 eligible observations found.")
            return DatasetQualityIndicators(
                total_records=len(build_result.records),
                eligible_records=0,
                excluded_records=excluded_count,
                missing_values_count=build_result.exclusion_summary.get("MISSING_FEATURE", 0)
                + build_result.exclusion_summary.get("MISSING_TARGET", 0),
                duplicate_records_count=build_result.exclusion_summary.get("DUPLICATE_RECORD", 0),
                potential_outliers_count=0,
                target_mean=None,
                target_std=None,
                target_min=None,
                target_max=None,
                feature_ranges={},
                warnings=warnings,
                is_valid_for_training=False,
            )

        if eligible_count < self.MIN_OBSERVATIONS_WARNING:
            warnings.append(
                f"Dataset contains only {eligible_count} observations. "
                "Predictive reliability and cross-validation stability may be low."
            )

        targets = np.array([r.target_value for r in eligible], dtype=float)
        t_mean = float(np.mean(targets))
        t_std = float(np.std(targets))
        t_min = float(np.min(targets))
        t_max = float(np.max(targets))

        if t_std == 0.0 or np.isnan(t_std):
            warnings.append("Target property has zero variance (all values are identical). Training cannot proceed.")
            is_valid = False

        # Outlier Detection (Z-score > 3.0)
        potential_outliers = 0
        if t_std > 0:
            z_scores = np.abs((targets - t_mean) / t_std)
            potential_outliers = int(np.sum(z_scores > 3.0))
            if potential_outliers > 0:
                warnings.append(f"Identified {potential_outliers} potential target outlier(s) (|Z| > 3.0).")

        # Feature Summary & Ranges
        feature_ranges: dict[str, dict[str, float]] = {}
        for fname in build_result.feature_names:
            vals = [r.feature_values[fname] for r in eligible if fname in r.feature_values]
            if len(vals) > 0:
                arr = np.array(vals, dtype=float)
                f_min, f_max = float(np.min(arr)), float(np.max(arr))
                f_mean, f_std = float(np.mean(arr)), float(np.std(arr))
                feature_ranges[fname] = {"min": f_min, "max": f_max, "mean": f_mean, "std": f_std}
                if f_std == 0.0:
                    warnings.append(f"Feature '{fname}' has zero variance across all eligible observations.")

        missing_count = (
            build_result.exclusion_summary.get("MISSING_FEATURE", 0)
            + build_result.exclusion_summary.get("MISSING_TARGET", 0)
        )
        duplicates_count = build_result.exclusion_summary.get("DUPLICATE_RECORD", 0)

        return DatasetQualityIndicators(
            total_records=len(build_result.records),
            eligible_records=eligible_count,
            excluded_records=excluded_count,
            missing_values_count=missing_count,
            duplicate_records_count=duplicates_count,
            potential_outliers_count=potential_outliers,
            target_mean=t_mean,
            target_std=t_std,
            target_min=t_min,
            target_max=t_max,
            feature_ranges=feature_ranges,
            warnings=warnings,
            is_valid_for_training=is_valid,
        )
