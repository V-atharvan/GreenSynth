"""
GreenSynth Analytics — Model Monitoring & Performance History Service (Phase 17)

Orchestrates model validation metric aggregation, signed prediction bias detection,
dataset shift monitoring, immutable performance snapshot logging, and model health evaluation.
"""

from __future__ import annotations

import logging
import uuid
import numpy as np
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml import MLModel, MLPrediction
from app.models.ml_validation import (
    ModelHealthSnapshot,
    ModelMonitoringEvent,
    PredictionValidation,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ModelMonitoringService:
    """Calculates model health, detects performance degradation/drift, and manages performance snapshots."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def evaluate_model_performance(
        self, model_id: uuid.UUID, min_validation_count: int = 3
    ) -> ModelHealthSnapshot:
        """
        Aggregates all validated predictions for a model, computes error metrics & bias,
        evaluates health status, and creates an immutable ModelHealthSnapshot.
        """
        # Fetch model
        res_m = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        model = res_m.scalar_one_or_none()
        if not model:
            raise ValueError(f"ML Model {model_id} not found.")

        # Fetch validated predictions linked to model
        res_v = await self.db.execute(
            select(PredictionValidation)
            .join(MLPrediction, PredictionValidation.prediction_id == MLPrediction.id)
            .where(
                MLPrediction.model_id == model_id,
                PredictionValidation.validation_status == "VALIDATED",
            )
        )
        validations: Sequence[PredictionValidation] = res_v.scalars().all()
        v_count = len(validations)

        if v_count < min_validation_count:
            # Insufficient data
            snapshot = ModelHealthSnapshot(
                id=uuid.uuid4(),
                model_id=model.id,
                model_version=model.version,
                validation_count=v_count,
                mae=0.0,
                rmse=0.0,
                r2=None,
                mean_error=0.0,
                median_absolute_error=0.0,
                interval_coverage=None,
                out_of_range_count=0,
                dataset_shift_indicator=False,
                performance_status="INSUFFICIENT_DATA",
            )
            self.db.add(snapshot)
            await self.db.commit()
            return snapshot

        # Extract predicted vs actual arrays
        actuals = np.array([v.actual_value for v in validations], dtype=float)
        predicteds = np.array([v.predicted_value for v in validations], dtype=float)
        errors = actuals - predicteds  # Signed errors
        abs_errors = np.abs(errors)

        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mean_err = float(np.mean(errors))  # Signed mean error for bias detection
        med_abs_err = float(np.median(abs_errors))

        # R^2 calculation if variance > 0
        tot_var = float(np.sum((actuals - np.mean(actuals)) ** 2))
        res_var = float(np.sum(errors ** 2))
        r2 = round(1.0 - (res_var / tot_var), 4) if tot_var > 1e-12 else None

        # Interval coverage
        cov_count = sum(1 for v in validations if v.actual_inside_interval is True)
        coverage = round(cov_count / v_count, 4) if v_count > 0 else None

        # Evaluate performance status against training metrics
        train_mae = float((model.metrics or {}).get("cv_mae", model.metrics.get("train_mae", mae)))
        
        status = "STABLE"
        event_message = None

        if mae > train_mae * 2.0:
            status = "CRITICAL"
            event_message = f"Model MAE ({mae:.4f}) is more than double baseline training MAE ({train_mae:.4f})."
        elif mae > train_mae * 1.4:
            status = "DEGRADED"
            event_message = f"Model MAE ({mae:.4f}) shows substantial degradation over baseline ({train_mae:.4f})."
        elif mae > train_mae * 1.15:
            status = "WARNING"
            event_message = f"Model MAE ({mae:.4f}) is slightly higher than baseline ({train_mae:.4f})."

        snapshot = ModelHealthSnapshot(
            id=uuid.uuid4(),
            model_id=model.id,
            model_version=model.version,
            validation_count=v_count,
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            r2=r2,
            mean_error=round(mean_err, 4),
            median_absolute_error=round(med_abs_err, 4),
            interval_coverage=coverage,
            out_of_range_count=0,
            dataset_shift_indicator=status in ("DEGRADED", "CRITICAL"),
            performance_status=status,
        )
        self.db.add(snapshot)

        # Log monitoring event if warning/degraded/critical
        if status in ("WARNING", "DEGRADED", "CRITICAL") and event_message:
            m_event = ModelMonitoringEvent(
                id=uuid.uuid4(),
                model_id=model.id,
                model_version=model.version,
                event_type="PERFORMANCE_DEGRADATION",
                severity="WARNING" if status == "WARNING" else "CRITICAL",
                message=event_message,
                metrics={"current_mae": mae, "baseline_mae": train_mae, "validation_count": v_count},
            )
            self.db.add(m_event)

        await self.audit.log(
            entity_type="ModelHealthSnapshot",
            entity_id=snapshot.id,
            action="EVALUATE_MODEL_HEALTH",
            changes={"model_id": str(model.id), "status": status, "mae": mae},
        )

        await self.db.commit()
        return snapshot

    async def get_latest_snapshot(self, model_id: uuid.UUID) -> ModelHealthSnapshot | None:
        res = await self.db.execute(
            select(ModelHealthSnapshot)
            .where(ModelHealthSnapshot.model_id == model_id)
            .order_by(ModelHealthSnapshot.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def list_snapshots(self, model_id: uuid.UUID) -> Sequence[ModelHealthSnapshot]:
        res = await self.db.execute(
            select(ModelHealthSnapshot)
            .where(ModelHealthSnapshot.model_id == model_id)
            .order_by(ModelHealthSnapshot.created_at.desc())
        )
        return res.scalars().all()
