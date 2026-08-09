"""
GreenSynth Analytics — Validation Orchestration Service

Orchestrates Holdout Validation, Prospective Experiment Tracking, Experimental Characterization Linking,
Validation Error Evaluation, Model Drift Monitoring, and Immutable Model Retraining Workflows.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import CalculatedProperty
from app.models.experiment import Experiment
from app.models.ml import MLDataset, MLDatasetRecord, MLModel, MLPrediction
from app.models.sample import Sample
from app.models.validation import (
    HoldoutValidation,
    ProspectiveExperiment,
    ValidationCriterion,
    ValidationResult,
)
from app.ml.schemas import MLDatasetCreateInput, MLDatasetFeatureSpec, MLTrainingRunCreateInput
from app.ml.services.dataset_service import MLDatasetService
from app.ml.services.training_service import MLTrainingService
from app.ml.validation.drift_detector import DriftDetector
from app.ml.validation.error_calculator import calculate_validation_errors
from app.ml.validation.holdout_validator import HoldoutValidator
from app.ml.validation.performance_history import PerformanceHistory, PerformanceHistoryCalculator
from app.ml.validation.prospective_validator import ProspectiveValidator
from app.ml.validation.schemas import (
    HoldoutValidationCreateInput,
    ModelRetrainInput,
    ProspectiveExperimentCreateInput,
)
from app.ml.validation.target_matcher import TargetMatcher
from app.ml.validation.unit_matcher import UnitMatcher
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


from app.models.ml_validation import (
    ConditionDeviation,
    ExperimentPredictionLink,
    PredictionValidation,
)
from app.ml.validation.condition_matcher import ConditionMatcherEngine
from app.ml.validation.model_monitoring_service import ModelMonitoringService


class ValidationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.holdout_validator = HoldoutValidator()
        self.prospective_validator = ProspectiveValidator()
        self.unit_matcher = UnitMatcher()
        self.target_matcher = TargetMatcher()
        self.drift_detector = DriftDetector()
        self.history_calculator = PerformanceHistoryCalculator()
        self.monitoring_service = ModelMonitoringService(db)

    async def validate_prediction_against_actual(
        self,
        prediction_id: uuid.UUID,
        actual_value: float,
        actual_target_property: str | None = None,
        actual_unit: str | None = None,
        experiment_id: uuid.UUID | None = None,
        sample_id: uuid.UUID | None = None,
        validated_by: str | None = None,
        source_type: str = "MEASURED_PROPERTY",
        actual_synthesis_params: dict[str, float] | None = None,
        notes: str | None = None,
    ) -> PredictionValidation:
        """
        Links an ML prediction to an actual laboratory measurement, enforces target and unit compatibility,
        computes error metrics & condition deviations, and evaluates model performance history.
        """
        res_p = await self.db.execute(select(MLPrediction).where(MLPrediction.id == prediction_id))
        pred = res_p.scalar_one_or_none()
        if not pred:
            raise ValueError(f"ML Prediction {prediction_id} not found.")

        # 1. Target Compatibility Gate
        pred_target = pred.predicted_property
        if actual_target_property and actual_target_property.lower() != pred_target.lower():
            raise ValueError(
                f"Target mismatch! Prediction target is '{pred_target}' but actual result is '{actual_target_property}'."
            )

        # 2. Unit Compatibility & Conversion Gate
        pred_unit = pred.unit
        actual_u = actual_unit or pred_unit
        conversion_factor = 1.0
        converted_a_val = float(actual_value)
        conversion_details = None

        if actual_u != pred_unit:
            # Check known unit conversions (e.g. S/m to S/cm)
            if actual_u.lower() in ("s/m", "siemens/m") and pred_unit.lower() in ("s/cm", "siemens/cm"):
                conversion_factor = 0.01
                converted_a_val = float(actual_value) * 0.01
                conversion_details = {"original_unit": actual_u, "converted_unit": pred_unit, "factor": 0.01}
            elif actual_u.lower() in ("s/cm", "siemens/cm") and pred_unit.lower() in ("s/m", "siemens/m"):
                conversion_factor = 100.0
                converted_a_val = float(actual_value) * 100.0
                conversion_details = {"original_unit": actual_u, "converted_unit": pred_unit, "factor": 100.0}

        p_val = float(pred.predicted_value)
        a_val = converted_a_val
        err = round(a_val - p_val, 4)  # Signed error
        abs_err = round(abs(a_val - p_val), 4)

        rel_err = round(abs_err / abs(a_val), 4) if abs(a_val) > 1e-12 else None
        pct_err = round((abs_err / abs(a_val)) * 100.0, 2) if abs(a_val) > 1e-12 else None

        # 3. Uncertainty Interval Check
        inside_interval = None
        if pred.uncertainty_lower is not None and pred.uncertainty_upper is not None:
            inside_interval = pred.uncertainty_lower <= a_val <= pred.uncertainty_upper

        # 4. Fetch Model ID & Dataset ID for provenance
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == pred.model_id))
        model = res_m.scalar_one_or_none()

        val_rec = PredictionValidation(
            id=uuid.uuid4(),
            prediction_id=pred.id,
            experiment_id=experiment_id,
            sample_id=sample_id,
            model_id=pred.model_id,
            model_version=pred.model_version,
            dataset_id=pred.dataset_id,
            dataset_version=model.dataset_version if model else "v1",
            target_property=pred_target,
            target_unit=pred_unit,
            predicted_value=p_val,
            actual_value=a_val,
            error=err,
            absolute_error=abs_err,
            relative_error=rel_err,
            percentage_error=pct_err,
            actual_inside_interval=inside_interval,
            validation_status="VALIDATED",
            source_type=source_type,
            quality_status="VALID" if conversion_details is None else "VALID_WITH_WARNING",
            conversion_details=conversion_details,
            validated_by=validated_by or "Dr. Chief Researcher",
            notes=notes,
        )
        self.db.add(val_rec)

        # 5. Link Prediction to Experiment
        if experiment_id:
            link = ExperimentPredictionLink(
                id=uuid.uuid4(),
                prediction_id=pred.id,
                experiment_id=experiment_id,
                link_type="PREDICTION_VALIDATION",
                created_by=validated_by,
                notes=notes,
            )
            self.db.add(link)

        # 6. Condition Deviations Evaluation
        if actual_synthesis_params and experiment_id:
            deviations, warnings = ConditionMatcherEngine.evaluate_condition_deviations(
                predicted_params=pred.input_parameters,
                actual_params=actual_synthesis_params,
            )
            for d in deviations:
                dev_rec = ConditionDeviation(
                    id=uuid.uuid4(),
                    prediction_id=pred.id,
                    experiment_id=experiment_id,
                    parameter_name=d["parameter_name"],
                    predicted_value=d["predicted_value"],
                    actual_value=d["actual_value"],
                    unit=d["unit"],
                    absolute_deviation=d["absolute_deviation"],
                    relative_deviation=d["relative_deviation"],
                    tolerance=d["tolerance"],
                    status=d["status"],
                )
                self.db.add(dev_rec)

        await self.audit.log(
            entity_type="PredictionValidation",
            entity_id=val_rec.id,
            action="PREDICTION_VALIDATED",
            notes=f"Predicted: {p_val}, Actual: {a_val}, Err: {err}, Abs Err: {abs_err}",
        )

        await self.db.flush()

        # 7. Evaluate Model Health & Update Performance Snapshot
        if model:
            await self.monitoring_service.evaluate_model_performance(model.id)

        await self.db.commit()
        return val_rec

    async def execute_holdout_validation(
        self, payload: HoldoutValidationCreateInput
    ) -> HoldoutValidation:
        """Executes Level 2 Holdout Prediction Validation."""
        # 1. Fetch Model & Training Records
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == payload.model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {payload.model_id} not found.")

        res_recs = await self.db.execute(
            select(MLDatasetRecord).where(MLDatasetRecord.dataset_id == model.dataset_id)
        )
        training_records = res_recs.scalars().all()

        # 2. Fetch Actual Calculated Property for Holdout Sample
        res_cp = await self.db.execute(
            select(CalculatedProperty)
            .where(
                CalculatedProperty.sample_id == payload.sample_id,
                CalculatedProperty.property_name == model.target_property,
            )
        )
        calc_prop = res_cp.scalar_one_or_none()
        if not calc_prop:
            raise ValueError(
                f"Actual calculated property '{model.target_property}' not found for sample {payload.sample_id}."
            )

        # 3. Fetch Criterion if provided
        criterion = None
        if payload.criterion_id:
            res_c = await self.db.execute(
                select(ValidationCriterion).where(ValidationCriterion.id == payload.criterion_id)
            )
            criterion = res_c.scalar_one_or_none()

        # 4. Predict on holdout sample feature parameters
        res_exp = await self.db.execute(select(Experiment).where(Experiment.id == payload.experiment_id))
        exp = res_exp.scalar_one_or_none()

        # Extract features
        from app.ml.services.prediction_service import MLPredictionService
        pred_service = MLPredictionService(self.db)
        
        # Get parameter values for holdout experiment
        from app.models.parameter import ExperimentParameter, ParameterDefinition
        p_res = await self.db.execute(
            select(ExperimentParameter, ParameterDefinition.parameter_code)
            .join(ParameterDefinition, ExperimentParameter.parameter_definition_id == ParameterDefinition.id)
            .where(ExperimentParameter.experiment_id == payload.experiment_id)
        )
        p_rows = p_res.all()
        param_vals = {}
        for ep, pcode in p_rows:
            v = ep.value_numeric if ep.value_numeric is not None else (float(ep.value) if ep.value else 0.0)
            param_vals[pcode] = v

        from app.ml.schemas import MLPredictInput
        pred_record = await pred_service.predict(
            model.id,
            payload=MLPredictInput(input_parameters=param_vals, notes="Holdout validation point"),
        )

        # 5. Run Holdout Validator (with zero data leakage check)
        holdout_record = self.holdout_validator.validate_holdout(
            model=model,
            training_records=training_records,
            holdout_experiment_id=payload.experiment_id,
            holdout_sample_id=payload.sample_id,
            predicted_value=pred_record.predicted_value,
            predicted_unit=pred_record.unit,
            actual_value=calc_prop.value,
            actual_property_name=calc_prop.property_name,
            actual_unit=calc_prop.unit,
            criterion=criterion,
            researcher=payload.researcher,
            notes=payload.notes,
        )

        self.db.add(holdout_record)
        await self.db.flush()

        # If holdout succeeded, persist a ValidationResult entity as well
        if holdout_record.status == "COMPLETED":
            vr = ValidationResult(
                prediction_id=pred_record.id,
                experiment_id=payload.experiment_id,
                sample_id=payload.sample_id,
                model_id=model.id,
                model_version=model.version,
                target_property=model.target_property,
                predicted_value=holdout_record.predicted_value,
                prediction_lower_bound=pred_record.uncertainty_lower,
                prediction_upper_bound=pred_record.uncertainty_upper,
                actual_value=holdout_record.actual_value,
                unit=holdout_record.unit,
                error=holdout_record.error,
                absolute_error=holdout_record.absolute_error,
                relative_error=holdout_record.relative_error,
                is_within_prediction_interval=(
                    pred_record.uncertainty_lower <= holdout_record.actual_value <= pred_record.uncertainty_upper
                    if pred_record.uncertainty_lower is not None and pred_record.uncertainty_upper is not None
                    else None
                ),
                criterion_id=payload.criterion_id,
                validation_type="HOLDOUT",
                validation_status="COMPLETE",
                researcher=payload.researcher,
                notes=payload.notes,
            )
            self.db.add(vr)
            await self.db.flush()

        await self.audit.log(
            entity_type="HoldoutValidation",
            entity_id=holdout_record.id,
            action="EXECUTE_HOLDOUT_VALIDATION",
            changes={"status": holdout_record.status, "abs_error": holdout_record.absolute_error},
        )
        return holdout_record

    async def create_prospective_experiment(
        self, payload: ProspectiveExperimentCreateInput
    ) -> ProspectiveExperiment:
        """Approves a model prediction for physical laboratory synthesis."""
        res_p = await self.db.execute(select(MLPrediction).where(MLPrediction.id == payload.prediction_id))
        pred = res_p.scalar_one_or_none()
        if not pred:
            raise ValueError(f"ML Prediction {payload.prediction_id} not found.")

        res_m = await self.db.execute(select(MLModel).where(MLModel.id == pred.model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {pred.model_id} not found.")

        prosp = ProspectiveExperiment(
            model_id=model.id,
            model_version=model.version,
            prediction_id=pred.id,
            project_id=payload.project_id,
            proposed_conditions=pred.input_parameters,
            researcher=payload.researcher,
            approval_status="APPROVED",
            validation_status="PENDING",
            notes=payload.notes,
        )
        self.db.add(prosp)
        await self.db.flush()

        await self.audit.log(
            entity_type="ProspectiveExperiment",
            entity_id=prosp.id,
            action="APPROVE_PROSPECTIVE_EXPERIMENT",
            changes={"prediction_id": str(pred.id), "status": "APPROVED"},
        )
        return prosp

    async def link_prospective_result(
        self,
        prospective_id: uuid.UUID,
        laboratory_experiment_id: uuid.UUID,
        sample_id: uuid.UUID,
        criterion_id: uuid.UUID | None = None,
        measurement_uncertainty: float | None = None,
        notes: str | None = None,
    ) -> ValidationResult:
        """Links laboratory experiment & characterization result to prospective prediction."""
        res_prosp = await self.db.execute(
            select(ProspectiveExperiment).where(ProspectiveExperiment.id == prospective_id)
        )
        prosp = res_prosp.scalar_one_or_none()
        if not prosp:
            raise ValueError(f"ProspectiveExperiment {prospective_id} not found.")

        res_m = await self.db.execute(select(MLModel).where(MLModel.id == prosp.model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {prosp.model_id} not found.")

        res_p = await self.db.execute(select(MLPrediction).where(MLPrediction.id == prosp.prediction_id))
        pred = res_p.scalar_one_or_none()
        if not pred:
            raise ValueError(f"ML Prediction {prosp.prediction_id} not found.")

        # Query Actual Calculated Property for Sample
        res_cp = await self.db.execute(
            select(CalculatedProperty)
            .where(
                CalculatedProperty.sample_id == sample_id,
                CalculatedProperty.property_name == model.target_property,
            )
        )
        calc_prop = res_cp.scalar_one_or_none()
        if not calc_prop:
            raise ValueError(
                f"Required characterization calculated property '{model.target_property}' not found for sample {sample_id}."
            )

        # Query Criterion if provided
        criterion = None
        if criterion_id:
            res_c = await self.db.execute(
                select(ValidationCriterion).where(ValidationCriterion.id == criterion_id)
            )
            criterion = res_c.scalar_one_or_none()

        # Target & Unit Matching
        t_match = self.target_matcher.match(model.target_property, calc_prop.property_name)
        if not t_match.is_match:
            raise ValueError(t_match.warning)

        u_res = self.unit_matcher.normalize(pred.predicted_value, pred.unit, calc_prop.value, calc_prop.unit)

        # Error Calculation & Criterion Evaluation
        err_res = calculate_validation_errors(
            predicted_value=u_res.normalized_predicted,
            actual_value=u_res.normalized_actual,
            lower_bound=pred.uncertainty_lower,
            upper_bound=pred.uncertainty_upper,
            criterion=criterion,
        )

        # Create ValidationResult Record
        vr = ValidationResult(
            prediction_id=pred.id,
            experiment_id=laboratory_experiment_id,
            sample_id=sample_id,
            model_id=model.id,
            model_version=model.version,
            target_property=model.target_property,
            predicted_value=round(u_res.normalized_predicted, 4),
            prediction_lower_bound=pred.uncertainty_lower,
            prediction_upper_bound=pred.uncertainty_upper,
            actual_value=round(u_res.normalized_actual, 4),
            actual_measurement_uncertainty=measurement_uncertainty,
            unit=u_res.normalized_unit,
            error=err_res.error,
            absolute_error=err_res.absolute_error,
            relative_error=err_res.relative_error,
            is_within_prediction_interval=err_res.is_within_prediction_interval,
            criterion_id=criterion_id,
            criterion_result=err_res.criterion_result,
            validation_type="PROSPECTIVE",
            validation_status="COMPLETE",
            researcher=prosp.researcher,
            notes=notes,
        )
        self.db.add(vr)

        # Update ProspectiveExperiment record
        prosp.laboratory_experiment_id = laboratory_experiment_id
        prosp.sample_id = sample_id
        prosp.actual_result = round(u_res.normalized_actual, 4)
        prosp.actual_unit = u_res.normalized_unit
        prosp.measurement_uncertainty = measurement_uncertainty
        prosp.validation_status = "COMPLETE"

        await self.db.flush()

        await self.audit.log(
            entity_type="ValidationResult",
            entity_id=vr.id,
            action="LINK_PROSPECTIVE_VALIDATION_RESULT",
            changes={
                "predicted": vr.predicted_value,
                "actual": vr.actual_value,
                "criterion_result": vr.criterion_result,
            },
        )
        return vr

    async def list_validation_results(
        self, model_id: uuid.UUID | None = None
    ) -> Sequence[ValidationResult]:
        q = select(ValidationResult).order_by(ValidationResult.timestamp.desc())
        if model_id:
            q = q.where(ValidationResult.model_id == model_id)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_performance_history(self, model_id: uuid.UUID) -> PerformanceHistory:
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {model_id} not found.")

        res_v = await self.db.execute(
            select(ValidationResult).where(ValidationResult.model_id == model_id)
        )
        val_results = res_v.scalars().all()

        history = self.history_calculator.calculate_history(model, val_results)

        # Check model drift
        if history.experimental_mae is not None:
            baseline_rmse = float(model.metrics.get("cv_rmse", 1.0))
            recent_errs = [r.absolute_error for r in val_results]
            drift_res = self.drift_detector.check_drift(baseline_rmse, recent_errs)
            if drift_res.has_drift:
                history.warnings.extend(drift_res.warnings)

        return history

    async def retrain_model(
        self, model_id: uuid.UUID, payload: ModelRetrainInput, created_by: str | None = None
    ) -> list[MLModel]:
        """
        Creates Dataset v2 including newly completed prospective experiments,
        and trains Model v2. Preserves Model v1 immutably.
        """
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        old_model = res_m.scalar_one_or_none()
        if not old_model:
            raise ValueError(f"ML Model {model_id} not found.")

        res_ds = await self.db.execute(select(MLDataset).where(MLDataset.id == old_model.dataset_id))
        old_ds = res_ds.scalar_one_or_none()
        if not old_ds:
            raise ValueError(f"ML Dataset {old_model.dataset_id} not found.")

        # 1. Create Dataset v2 via MLDatasetService
        ds_service = MLDatasetService(self.db)
        feat_specs = [
            MLDatasetFeatureSpec(
                feature_name=f["feature_name"],
                source_parameter=f["source_parameter"],
                unit=f["unit"],
                data_type=f.get("data_type", "NUMBER"),
            )
            for f in old_ds.features
        ]
        new_ds_payload = MLDatasetCreateInput(
            project_id=old_ds.project_id,
            name=f"{old_ds.name} (Retrained v2)",
            description=f"Retrained dataset incorporating new prospective validation records. Original notes: {payload.notes or ''}",
            target_property=old_ds.target_property,
            target_type=old_ds.target_type,
            target_unit=old_ds.target_unit,
            features=feat_specs,
        )
        new_ds, _quality = await ds_service.create_dataset(new_ds_payload, created_by=created_by)
        new_ds.version = "v2"

        # 2. Run Training for new model v2
        tr_service = MLTrainingService(self.db)
        train_payload = MLTrainingRunCreateInput(
            dataset_id=new_ds.id,
            model_types=[old_model.model_type],
            scaling=old_model.preprocessing_config.get("scaling", "STANDARD"),
            cv_folds=5,
            random_seed=old_model.random_seed,
            hyperparameters={old_model.model_type: old_model.hyperparameters},
        )
        new_models = await tr_service.run_training(train_payload, created_by=created_by)
        for nm in new_models:
            nm.version = "2.0"
            nm.name = f"{nm.name} (v2)"

        await self.db.flush()

        await self.audit.log(
            entity_type="MLModel",
            entity_id=old_model.id,
            action="REQUEST_MODEL_RETRAINING",
            changes={"old_version": "1.0", "new_dataset_id": str(new_ds.id)},
        )
        return new_models
