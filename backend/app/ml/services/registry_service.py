"""
GreenSynth Analytics — ML Registry Service

Manages registered ML models, model lifecycle transitions (TRAINED -> VALIDATED -> PRODUCTION_CANDIDATE / REJECTED),
and model comparison queries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml import MLModel
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MLRegistryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def get_model(self, model_id: uuid.UUID) -> MLModel:
        res = await self.db.execute(select(MLModel).where(MLModel.id == model_id))
        m = res.scalar_one_or_none()
        if m is None:
            raise ValueError(f"ML Model {model_id} not found.")
        return m

    async def list_models(
        self, dataset_id: uuid.UUID | None = None, status: str | None = None
    ) -> Sequence[MLModel]:
        q = select(MLModel).order_by(MLModel.created_at.desc())
        if dataset_id:
            q = q.where(MLModel.dataset_id == dataset_id)
        if status:
            q = q.where(MLModel.status == status)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def approve_model(
        self, model_id: uuid.UUID, approved_by: str | None = None, notes: str | None = None
    ) -> MLModel:
        """Transitions model status to PRODUCTION_CANDIDATE after researcher approval."""
        model = await self.get_model(model_id)
        if model.status == "REJECTED":
            raise ValueError("Cannot approve a rejected model.")

        model.status = "PRODUCTION_CANDIDATE"
        model.approved_by = approved_by or "Researcher"
        model.approved_at = datetime.utcnow()
        model.approval_notes = notes

        await self.db.flush()

        await self.audit.log(
            entity_type="MLModel",
            entity_id=model.id,
            action="APPROVE_ML_MODEL",
            changes={"status": "PRODUCTION_CANDIDATE", "notes": notes},
        )
        return model

    async def reject_model(
        self, model_id: uuid.UUID, notes: str | None = None
    ) -> MLModel:
        """Transitions model status to REJECTED."""
        model = await self.get_model(model_id)
        model.status = "REJECTED"
        model.approval_notes = notes

        await self.db.flush()

        await self.audit.log(
            entity_type="MLModel",
            entity_id=model.id,
            action="REJECT_ML_MODEL",
            changes={"status": "REJECTED", "notes": notes},
        )
        return model
