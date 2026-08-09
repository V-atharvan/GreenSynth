"""
GreenSynth Analytics — ML Training Service

Orchestrates model training, cross-validation, evaluation, artifact serialization,
and registration in the model registry.
"""

from __future__ import annotations

import logging
import uuid
import numpy as np
import sklearn
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml import MLDataset, MLDatasetRecord, MLModel, MLTrainingRun
from app.ml.evaluation.cross_validation import run_cross_validation
from app.ml.evaluation.diagnostics import generate_diagnostics
from app.ml.evaluation.metrics import calculate_regression_metrics, check_overfitting
from app.ml.models.base import BaseMLModel
from app.ml.models.baseline import MeanBaselineModel
from app.ml.models.linear import LinearRegressionModel
from app.ml.models.ridge import RidgeRegressionModel
from app.ml.models.lasso import LassoRegressionModel
from app.ml.models.random_forest import RandomForestModel
from app.ml.models.gradient_boosting import GradientBoostingModel
from app.ml.preprocessing.pipeline import PreprocessingPipeline
from app.ml.registry.artifact_store import ModelArtifactStore
from app.ml.schemas import MLTrainingRunCreateInput
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MLTrainingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.artifact_store = ModelArtifactStore()

    def _instantiate_model(self, model_type: str, hyperparams: dict[str, Any] | None = None) -> BaseMLModel:
        hparams = hyperparams or {}
        if model_type == "MEAN_BASELINE":
            return MeanBaselineModel(hyperparameters=hparams)
        elif model_type == "LINEAR_REGRESSION":
            return LinearRegressionModel(hyperparameters=hparams)
        elif model_type == "RIDGE":
            return RidgeRegressionModel(hyperparameters=hparams)
        elif model_type == "LASSO":
            return LassoRegressionModel(hyperparameters=hparams)
        elif model_type == "RANDOM_FOREST":
            return RandomForestModel(hyperparameters=hparams)
        elif model_type == "GRADIENT_BOOSTING":
            return GradientBoostingModel(hyperparameters=hparams)
        else:
            raise ValueError(f"Unsupported ML model type: '{model_type}'")

    async def run_training(
        self, payload: MLTrainingRunCreateInput, created_by: str | None = None
    ) -> list[MLModel]:
        """
        Trains and registers candidate ML models for a given MLDataset.
        """
        # 1. Fetch Dataset & Records
        res_ds = await self.db.execute(select(MLDataset).where(MLDataset.id == payload.dataset_id))
        dataset = res_ds.scalar_one_or_none()
        if dataset is None:
            raise ValueError(f"ML Dataset {payload.dataset_id} not found.")

        # Mark dataset IMMUTABLE once training begins
        dataset.status = "IMMUTABLE"

        res_recs = await self.db.execute(
            select(MLDatasetRecord)
            .where(MLDatasetRecord.dataset_id == dataset.id, MLDatasetRecord.is_eligible == True)
        )
        eligible_records = res_recs.scalars().all()

        if len(eligible_records) == 0:
            raise ValueError(f"Cannot train models: dataset '{dataset.name}' has 0 eligible observations.")

        feature_names = [f["feature_name"] for f in dataset.features]
        n_samples = len(eligible_records)

        # 2. Extract Feature Matrix X and Target Vector y
        X_rows: list[list[float]] = []
        y_vals: list[float] = []
        exp_ids: list[str] = []
        sample_ids: list[str] = []

        for rec in eligible_records:
            row = [float(rec.feature_values.get(fname, 0.0)) for fname in feature_names]
            X_rows.append(row)
            y_vals.append(float(rec.target_value))
            exp_ids.append(str(rec.experiment_id))
            sample_ids.append(str(rec.sample_id))

        X = np.array(X_rows, dtype=float)
        y = np.array(y_vals, dtype=float)

        registered_models: list[MLModel] = []
        lib_versions = {
            "scikit-learn": sklearn.__version__,
            "numpy": np.__version__,
        }

        for m_type in payload.model_types:
            hparams = (payload.hyperparameters or {}).get(m_type, {})
            hparams["random_state"] = payload.random_seed

            # Create TrainingRun entity
            t_run = MLTrainingRun(
                dataset_id=dataset.id,
                dataset_version=dataset.version,
                model_type=m_type,
                preprocessing_version="v1",
                hyperparameters=hparams,
                random_seed=payload.random_seed,
                cv_folds=payload.cv_folds,
                status="RUNNING",
                started_at=datetime.utcnow(),
            )
            self.db.add(t_run)
            await self.db.flush()

            # 3. Perform Cross-Validation
            cv_res = run_cross_validation(
                model_factory=lambda: self._instantiate_model(m_type, hparams),
                X=X,
                y=y,
                feature_names=feature_names,
                scaling=payload.scaling,
                cv_folds=payload.cv_folds,
                groups=exp_ids,
                random_seed=payload.random_seed,
            )

            # 4. Fit Full Dataset Model
            pipe = PreprocessingPipeline(scaling=payload.scaling)
            X_scaled = pipe.fit_transform(X, feature_names)

            full_model = self._instantiate_model(m_type, hparams)
            full_model.fit(X_scaled, y, feature_names)

            # 5. Evaluate Full Training Performance
            y_pred_full = full_model.predict(X_scaled)
            train_m = calculate_regression_metrics(y, y_pred_full)

            # 6. Overfitting & Low Data Warnings
            is_overfit = check_overfitting(train_m.r2, cv_res.mean_r2)
            is_low_data = n_samples < 15

            t_run.training_metrics = train_m.to_dict()
            t_run.validation_metrics = cv_res.to_dict()
            t_run.overfitting_warning = is_overfit
            t_run.low_data_warning = is_low_data
            t_run.status = "COMPLETED"
            t_run.completed_at = datetime.utcnow()

            await self.db.flush()

            # 7. Generate Diagnostics
            diagnostics = generate_diagnostics(
                model=full_model,
                X=X_scaled,
                y_actual=y,
                y_pred=y_pred_full,
                feature_names=feature_names,
                sample_ids=sample_ids,
            )

            # 8. Compute feature min/max ranges for out-of-domain checking
            feature_ranges = {}
            for idx, fname in enumerate(feature_names):
                vals_col = X[:, idx]
                feature_ranges[fname] = {
                    "min": round(float(np.min(vals_col)), 4),
                    "max": round(float(np.max(vals_col)), 4),
                    "mean": round(float(np.mean(vals_col)), 4),
                    "std": round(float(np.std(vals_col)), 4),
                }

            # 9. Save Artifact to Disk
            model_id = uuid.uuid4()
            art_path, art_hash = self.artifact_store.save_artifact(
                model_id=str(model_id),
                model=full_model,
                preprocessing_pipeline=pipe,
                metadata={
                    "dataset_id": str(dataset.id),
                    "feature_names": feature_names,
                    "target_property": dataset.target_property,
                    "target_unit": dataset.target_unit,
                    "training_feature_ranges": feature_ranges,
                },
            )

            # 10. Create MLModel Record
            overall_metrics = {
                "train_mae": round(train_m.mae, 4),
                "train_rmse": round(train_m.rmse, 4),
                "train_r2": round(train_m.r2, 4),
                "cv_mae": round(cv_res.mean_mae, 4),
                "cv_rmse": round(cv_res.mean_rmse, 4),
                "cv_r2": round(cv_res.mean_r2, 4),
                "n_samples": n_samples,
                "overfitting_warning": is_overfit,
                "low_data_warning": is_low_data,
                "diagnostics": diagnostics,
            }

            model_record = MLModel(
                id=model_id,
                training_run_id=t_run.id,
                dataset_id=dataset.id,
                dataset_version=dataset.version,
                name=f"{dataset.name} — {m_type}",
                model_type=m_type,
                version="1.0",
                target_property=dataset.target_property,
                target_type=dataset.target_type,
                target_unit=dataset.target_unit,
                feature_names=feature_names,
                feature_specs=dataset.features,
                preprocessing_config=pipe.get_config(),
                hyperparameters=hparams,
                random_seed=payload.random_seed,
                artifact_path=art_path,
                artifact_hash=art_hash,
                feature_ranges_json=feature_ranges,
                metrics=overall_metrics,
                feature_importance=diagnostics["feature_importance"],
                library_versions=lib_versions,
                status="VALIDATED" if cv_res.mean_r2 > 0.0 else "TRAINED",
                created_by=created_by,
            )
            self.db.add(model_record)
            await self.db.flush()

            registered_models.append(model_record)

            await self.audit.log(
                entity_type="MLModel",
                entity_id=model_record.id,
                action="TRAIN_ML_MODEL",
                changes={"model_type": m_type, "cv_r2": cv_res.mean_r2},
            )

        return registered_models

    async def get_training_run(self, run_id: uuid.UUID) -> MLTrainingRun:
        res = await self.db.execute(select(MLTrainingRun).where(MLTrainingRun.id == run_id))
        tr = res.scalar_one_or_none()
        if tr is None:
            raise ValueError(f"Training run {run_id} not found.")
        return tr

    async def list_training_runs(self, dataset_id: uuid.UUID) -> Sequence[MLTrainingRun]:
        res = await self.db.execute(
            select(MLTrainingRun)
            .where(MLTrainingRun.dataset_id == dataset_id)
            .order_by(MLTrainingRun.started_at.desc())
        )
        return res.scalars().all()
