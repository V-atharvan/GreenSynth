"""
GreenSynth Analytics — Model Lifecycle & Promotion Service

Manages model performance snapshots across versions and manual model promotion/retirement.
Enforces strict researcher review for model promotion (no automatic replacement).
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.ml import MLModel
from app.models.validation import ModelPerformanceSnapshot


class ModelLifecycleService:
    """
    Manages model performance tracking across versions and manual promotion workflows.
    """

    @staticmethod
    def record_performance_snapshot(
        db: Session,
        model_id: uuid.UUID,
        model_version: str,
        dataset_version: str,
        evaluation_type: str,  # TRAINING, CROSS_VALIDATION, TEST, PROSPECTIVE_VALIDATION, FULL_VALIDATION
        target_property: str,
        sample_count: int,
        mae: Optional[float] = None,
        rmse: Optional[float] = None,
        r2: Optional[float] = None,
        mean_error: Optional[float] = None,
    ) -> ModelPerformanceSnapshot:
        """
        Creates a ModelPerformanceSnapshot for historical performance comparison across model versions.
        """
        snapshot = ModelPerformanceSnapshot(
            id=uuid.uuid4(),
            model_id=model_id,
            model_version=model_version,
            dataset_version=dataset_version,
            evaluation_type=evaluation_type,
            target_property=target_property,
            sample_count=sample_count,
            mae=mae,
            rmse=rmse,
            r2=r2,
            mean_error=mean_error,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def get_model_performance_history(db: Session, model_id: uuid.UUID) -> List[ModelPerformanceSnapshot]:
        """
        Retrieves all performance snapshots for a given model.
        """
        return list(
            db.scalars(
                select(ModelPerformanceSnapshot)
                .where(ModelPerformanceSnapshot.model_id == model_id)
                .order_by(ModelPerformanceSnapshot.created_at.desc())
            ).all()
        )

    @staticmethod
    def promote_model(
        db: Session,
        model_id: uuid.UUID,
        promoted_by: str,
        notes: Optional[str] = None,
    ) -> MLModel:
        """
        Manually promotes a model to ACTIVE state with explicit researcher approval.
        Retires any currently ACTIVE model for the same target property.
        """
        target_model = db.get(MLModel, model_id)
        if not target_model:
            raise ValueError(f"MLModel {model_id} not found.")

        # Retire existing active models for this target property
        existing_active = db.scalars(
            select(MLModel).where(
                MLModel.target_property == target_model.target_property,
                MLModel.status == "ACTIVE",
                MLModel.id != model_id,
            )
        ).all()

        for old_model in existing_active:
            old_model.status = "RETIRED"

        target_model.status = "ACTIVE"
        target_model.approved_by = promoted_by

        db.commit()
        db.refresh(target_model)
        return target_model

    @staticmethod
    def retire_model(db: Session, model_id: uuid.UUID, retired_by: str) -> MLModel:
        """
        Retires a model. Historical recommendations and validation records remain linked.
        """
        target_model = db.get(MLModel, model_id)
        if not target_model:
            raise ValueError(f"MLModel {model_id} not found.")

        target_model.status = "RETIRED"
        db.commit()
        db.refresh(target_model)
        return target_model
