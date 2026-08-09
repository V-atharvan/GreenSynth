"""
GreenSynth Analytics — Validation Criterion Service

Database service for creating, retrieving, and listing researcher-defined validation criteria.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import ValidationCriterion
from app.ml.validation.schemas import ValidationCriterionCreateInput
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class CriterionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def create_criterion(
        self, payload: ValidationCriterionCreateInput, created_by: str | None = None
    ) -> ValidationCriterion:
        crit = ValidationCriterion(
            property_name=payload.property_name,
            metric=payload.metric.upper(),
            threshold=payload.threshold,
            unit=payload.unit,
            comparison_operator=payload.comparison_operator,
            description=payload.description,
            created_by=created_by,
        )
        self.db.add(crit)
        await self.db.flush()

        await self.audit.log(
            entity_type="ValidationCriterion",
            entity_id=crit.id,
            action="CREATE_VALIDATION_CRITERION",
            changes={"property_name": crit.property_name, "threshold": crit.threshold},
        )
        return crit

    async def get_criterion(self, criterion_id: uuid.UUID) -> ValidationCriterion:
        res = await self.db.execute(
            select(ValidationCriterion).where(ValidationCriterion.id == criterion_id)
        )
        crit = res.scalar_one_or_none()
        if crit is None:
            raise ValueError(f"ValidationCriterion {criterion_id} not found.")
        return crit

    async def list_criteria(
        self, property_name: str | None = None
    ) -> Sequence[ValidationCriterion]:
        q = select(ValidationCriterion).order_by(ValidationCriterion.created_at.desc())
        if property_name:
            q = q.where(ValidationCriterion.property_name == property_name)
        res = await self.db.execute(q)
        return res.scalars().all()
