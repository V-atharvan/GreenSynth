"""
GreenSynth Analytics — Sample Service

Business logic for sample management operations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sample import Sample
from app.schemas.sample import SampleCreate, SampleUpdate
from app.services.experiment_service import ExperimentNotFoundError, ExperimentService

logger = logging.getLogger(__name__)


class SampleNotFoundError(Exception):
    """Raised when a sample cannot be found."""


class SampleCodeConflictError(Exception):
    """Raised when sample_code is already in use."""


class SampleService:
    """Service layer for sample management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        experiment_id: uuid.UUID | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> Sequence[Sample]:
        """Return samples with optional experiment/status filters."""
        q = (
            select(Sample)
            .options(selectinload(Sample.experiment))
            .order_by(Sample.created_at.desc())
        )
        if experiment_id:
            q = q.where(Sample.experiment_id == experiment_id)
        if status:
            q = q.where(Sample.status == status)
        if not include_archived:
            q = q.where(Sample.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, sample_id: uuid.UUID) -> Sample:
        """Return sample by UUID, raising SampleNotFoundError if missing."""
        result = await self.db.execute(
            select(Sample)
            .options(selectinload(Sample.experiment))
            .where(Sample.id == sample_id)
        )
        sample = result.scalar_one_or_none()
        if sample is None:
            raise SampleNotFoundError(f"Sample {sample_id} not found.")
        return sample

    async def get_by_code(self, sample_code: str) -> Sample | None:
        result = await self.db.execute(
            select(Sample).where(Sample.sample_code == sample_code)
        )
        return result.scalar_one_or_none()

    async def create(self, data: SampleCreate) -> Sample:
        """Create a new sample. Validates parent experiment exists."""
        experiment_service = ExperimentService(self.db)
        try:
            await experiment_service.get_by_id(data.experiment_id)
        except ExperimentNotFoundError:
            raise ExperimentNotFoundError(
                f"Cannot create sample: experiment {data.experiment_id} not found."
            )

        existing = await self.get_by_code(data.sample_code)
        if existing is not None:
            raise SampleCodeConflictError(
                f"Sample code '{data.sample_code}' is already in use."
            )

        sample = Sample(
            experiment_id=data.experiment_id,
            sample_code=data.sample_code,
            name=data.name,
            material=data.material,
            description=data.description,
            status=data.status.value,
            notes=data.notes,
        )
        self.db.add(sample)
        await self.db.flush()
        await self.db.refresh(sample)
        logger.info("Sample created: %s (%s)", sample.sample_code, sample.id)
        return sample

    async def update(self, sample_id: uuid.UUID, data: SampleUpdate) -> Sample:
        """Update sample fields. Only non-None fields are changed."""
        sample = await self.get_by_id(sample_id)
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(sample, field):
                setattr(sample, field, value.value if hasattr(value, "value") else value)
        await self.db.flush()
        await self.db.refresh(sample)
        logger.info("Sample updated: %s", sample_id)
        return sample

    async def delete(self, sample_id: uuid.UUID) -> None:
        """Archive a sample (soft delete)."""
        sample = await self.get_by_id(sample_id)
        sample.status = "ARCHIVED"
        await self.db.flush()
        logger.info("Sample archived: %s", sample_id)

    async def count(
        self,
        experiment_id: uuid.UUID | None = None,
        include_archived: bool = False,
    ) -> int:
        q = select(func.count(Sample.id))
        if experiment_id:
            q = q.where(Sample.experiment_id == experiment_id)
        if not include_archived:
            q = q.where(Sample.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalar_one()
