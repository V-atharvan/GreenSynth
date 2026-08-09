"""
GreenSynth Analytics — Holdout Prediction Validator

Validates model predictions against holdout experiments (experiments deliberately excluded from model training).
Verifies strict data leakage protection (fails validation if holdout experiment was present in training dataset).
"""

from __future__ import annotations

import logging
import uuid

from app.ml.validation.error_calculator import calculate_validation_errors
from app.ml.validation.target_matcher import TargetMatcher
from app.ml.validation.unit_matcher import UnitMatcher
from app.models.ml import MLDatasetRecord, MLModel
from app.models.validation import HoldoutValidation, ValidationCriterion

logger = logging.getLogger(__name__)


class HoldoutValidator:
    """
    Executes Level 2 Holdout Prediction Validation.
    """

    def __init__(self) -> None:
        self.unit_matcher = UnitMatcher()
        self.target_matcher = TargetMatcher()

    def validate_holdout(
        self,
        model: MLModel,
        training_records: list[MLDatasetRecord],
        holdout_experiment_id: uuid.UUID,
        holdout_sample_id: uuid.UUID,
        predicted_value: float,
        predicted_unit: str,
        actual_value: float,
        actual_property_name: str,
        actual_unit: str,
        criterion: ValidationCriterion | None = None,
        researcher: str | None = None,
        notes: str | None = None,
    ) -> HoldoutValidation:
        # 1. Data Leakage Verification
        trained_exp_ids = {r.experiment_id for r in training_records if r.is_eligible}
        if holdout_experiment_id in trained_exp_ids:
            logger.error("Data Leakage Detected: Holdout experiment %s was included in training dataset!", holdout_experiment_id)
            return HoldoutValidation(
                model_id=model.id,
                model_version=model.version,
                dataset_id=model.dataset_id,
                experiment_id=holdout_experiment_id,
                sample_id=holdout_sample_id,
                target_property=model.target_property,
                predicted_value=predicted_value,
                actual_value=actual_value,
                unit=actual_unit,
                error=0.0,
                absolute_error=0.0,
                relative_error=None,
                status="FAILED_LEAKAGE",
                researcher=researcher,
                notes=f"Data Leakage Violation: Experiment {holdout_experiment_id} was present in the model training dataset.",
            )

        # 2. Target Property Matching
        t_match = self.target_matcher.match(model.target_property, actual_property_name)
        if not t_match.is_match:
            return HoldoutValidation(
                model_id=model.id,
                model_version=model.version,
                dataset_id=model.dataset_id,
                experiment_id=holdout_experiment_id,
                sample_id=holdout_sample_id,
                target_property=model.target_property,
                predicted_value=predicted_value,
                actual_value=actual_value,
                unit=actual_unit,
                error=0.0,
                absolute_error=0.0,
                relative_error=None,
                status="TARGET_MISMATCH",
                researcher=researcher,
                notes=t_match.warning,
            )

        # 3. Unit Normalization
        u_res = self.unit_matcher.normalize(predicted_value, predicted_unit, actual_value, actual_unit)

        # 4. Error Calculation
        err_res = calculate_validation_errors(
            predicted_value=u_res.normalized_predicted,
            actual_value=u_res.normalized_actual,
            criterion=criterion,
        )

        return HoldoutValidation(
            model_id=model.id,
            model_version=model.version,
            dataset_id=model.dataset_id,
            experiment_id=holdout_experiment_id,
            sample_id=holdout_sample_id,
            target_property=model.target_property,
            predicted_value=round(u_res.normalized_predicted, 4),
            actual_value=round(u_res.normalized_actual, 4),
            unit=u_res.normalized_unit,
            error=err_res.error,
            absolute_error=err_res.absolute_error,
            relative_error=err_res.relative_error,
            status="COMPLETED",
            researcher=researcher,
            notes=notes,
        )
