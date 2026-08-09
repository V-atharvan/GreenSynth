"""
GreenSynth Analytics — ML Prediction Service

Loads registered model artifacts, validates input features, computes predictions,
evaluates applicability domain bounds, and calculates prediction uncertainty intervals.
"""

from __future__ import annotations

import logging
import uuid
import numpy as np
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml import MLDatasetRecord, MLModel, MLPrediction
from app.ml.prediction.applicability import ApplicabilityChecker
from app.ml.prediction.uncertainty import UncertaintyEstimator
from app.ml.registry.artifact_store import ModelArtifactStore
from app.ml.schemas import MLPredictInput
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MLPredictionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.artifact_store = ModelArtifactStore()
        self.applicability_checker = ApplicabilityChecker()
        self.uncertainty_estimator = UncertaintyEstimator()

    async def predict(
        self, model_id: uuid.UUID, payload: MLPredictInput, created_by: str | None = None
    ) -> MLPrediction:
        """
        Loads model artifact, validates input parameters against training domain,
        computes point prediction & uncertainty interval, and logs prediction.
        """
        # 1. Fetch MLModel metadata
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        model_record = res_m.scalar_one_or_none()
        if model_record is None:
            raise ValueError(f"ML Model {model_id} not found.")

        # 2. Check model status
        if model_record.status == "REJECTED":
            raise ValueError("Cannot generate predictions using a REJECTED model.")

        feature_names = model_record.feature_names
        input_vals = payload.input_parameters

        # 3. Validate feature inputs
        missing = [fn for fn in feature_names if fn not in input_vals]
        if missing:
            raise ValueError(f"Missing required input parameters: {missing}")

        # 4. Extract Training Feature Min/Max Ranges for Applicability Check
        res_recs = await self.db.execute(
            select(MLDatasetRecord)
            .where(MLDatasetRecord.dataset_id == model_record.dataset_id, MLDatasetRecord.is_eligible == True)
        )
        eligible_records = res_recs.scalars().all()
        training_ranges: dict[str, dict[str, float]] = {}

        for fname in feature_names:
            vals = [float(r.feature_values[fname]) for r in eligible_records if fname in r.feature_values]
            if vals:
                training_ranges[fname] = {"min": float(min(vals)), "max": float(max(vals))}
            else:
                training_ranges[fname] = {"min": 0.0, "max": 1000.0}

        app_res = self.applicability_checker.check_applicability(
            input_values=input_vals,
            training_feature_ranges=training_ranges,
            model_status=model_record.status,
        )

        # 5. Load Model Artifact from Disk with SHA256 checksum check
        bundle = self.artifact_store.load_artifact(
            model_record.artifact_path, expected_hash=model_record.artifact_hash
        )
        fitted_model = bundle["model"]
        pipe = bundle["pipeline"]

        # 6. Preprocess & Predict
        x_row = [float(input_vals[fn]) for fn in feature_names]
        X_in = np.array([x_row], dtype=float)
        X_scaled = pipe.transform(X_in)

        raw_pred = fitted_model.predict(X_scaled)
        pred_val = float(raw_pred[0])

        # 7. Uncertainty Estimation
        val_rmse = float(model_record.metrics.get("cv_rmse", 1.0))
        unc_res = self.uncertainty_estimator.estimate_uncertainty(
            predicted_value=pred_val,
            validation_rmse=val_rmse,
            confidence_factor=1.96,
        )

        # 8. Create MLPrediction ORM Record
        prediction = MLPrediction(
            model_id=model_record.id,
            model_version=model_record.version,
            dataset_id=model_record.dataset_id,
            input_parameters=input_vals,
            predicted_property=model_record.target_property,
            predicted_value=round(pred_val, 4),
            unit=model_record.target_unit,
            uncertainty_lower=unc_res.uncertainty_lower,
            uncertainty_upper=unc_res.uncertainty_upper,
            uncertainty_method=unc_res.method,
            applicability_status=app_res.status,
            applicability_details=app_res.feature_coverage,
            warnings=app_res.warnings,
            notes=payload.notes,
            created_by=created_by,
        )
        self.db.add(prediction)
        await self.db.flush()

        await self.audit.log(
            entity_type="MLPrediction",
            entity_id=prediction.id,
            action="GENERATE_PREDICTION",
            changes={
                "model_id": str(model_record.id),
                "property": model_record.target_property,
                "predicted_value": prediction.predicted_value,
                "status": app_res.status,
            },
        )
        return prediction

    async def list_predictions(
        self, model_id: uuid.UUID | None = None
    ) -> Sequence[MLPrediction]:
        q = select(MLPrediction).order_by(MLPrediction.created_at.desc())
        if model_id:
            q = q.where(MLPrediction.model_id == model_id)
        res = await self.db.execute(q)
        return res.scalars().all()
