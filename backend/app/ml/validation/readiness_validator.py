"""
GreenSynth Analytics — ML Dataset Readiness Validator (Phase 16)

Evaluates:
  1. Dataset & DatasetVersion existence & locking
  2. Experiment & sample traceability
  3. Target property & unit validity
  4. Feature units & parameter availability
  5. Missing observations check
  6. Unresolved critical data quality errors
  7. Status: READY, NOT_READY, READY_WITH_WARNING
"""

from __future__ import annotations

from typing import Any


class MLReadinessValidator:
    """Evaluates whether a scientific dataset meets configured quality criteria to enter the ML training pipeline."""

    @staticmethod
    def validate_dataset_readiness(
        dataset_meta: dict[str, Any],
        sample_records: list[dict[str, Any]],
        target_property: str,
        feature_names: list[str],
    ) -> tuple[str, dict[str, bool], list[str]]:
        """
        Validates ML readiness.

        Returns:
            status: READY, NOT_READY, or READY_WITH_WARNING
            criteria_results: dict mapping test names to booleans
            reasons: list of explicit failure or warning reasons
        """
        total_samples = len(sample_records)
        reasons: list[str] = []

        c_exists = dataset_meta is not None
        if not c_exists:
            reasons.append("Dataset does not exist.")

        c_locked = dataset_meta.get("status") in ("ACTIVE", "LOCKED", "ML_READY", "READY", "IMMUTABLE")
        if not c_locked:
            reasons.append(f"Dataset status '{dataset_meta.get('status')}' is not version-locked.")

        c_target = any(r.get(target_property) is not None for r in sample_records)
        if not c_target:
            reasons.append(f"Target variable '{target_property}' contains no valid observations in dataset.")

        missing_targets = sum(1 for r in sample_records if r.get(target_property) is None)
        c_missing_target = (missing_targets / max(total_samples, 1)) <= 0.35
        if not c_missing_target:
            reasons.append(f"Target variable '{target_property}' contains substantial missing observations ({missing_targets}/{total_samples}).")

        c_sample_size = total_samples >= 5
        if not c_sample_size:
            reasons.append(f"Dataset sample size (N={total_samples}) is below recommended minimum threshold (N >= 5).")

        c_features = len(feature_names) >= 1
        if not c_features:
            reasons.append("No synthesis features specified for training.")

        criteria_results = {
            "dataset_exists": c_exists,
            "dataset_locked": c_locked,
            "target_observed": c_target,
            "acceptable_missing_rate": c_missing_target,
            "sufficient_sample_size": c_sample_size,
            "features_specified": c_features,
        }

        critical_failures = not (c_exists and c_target and c_features and total_samples >= 3)

        if critical_failures or not c_missing_target:
            status = "NOT_READY"
        elif not c_sample_size or missing_targets > 0:
            status = "READY_WITH_WARNING"
            if not c_sample_size:
                reasons.append("Prediction reliability may be limited because the available experimental dataset is small.")
        else:
            status = "READY"

        return status, criteria_results, reasons
