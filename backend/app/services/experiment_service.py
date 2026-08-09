"""
GreenSynth Analytics — Experiment Service

Business logic for experiment management operations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate
from app.services.project_service import ProjectNotFoundError, ProjectService

logger = logging.getLogger(__name__)


class ExperimentNotFoundError(Exception):
    """Raised when an experiment cannot be found."""


class ExperimentCodeConflictError(Exception):
    """Raised when experiment_code is already in use."""


class ExperimentService:
    """Service layer for experiment management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        project_id: uuid.UUID | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> Sequence[Experiment]:
        """Return experiments with optional project/status filters."""
        q = (
            select(Experiment)
            .options(selectinload(Experiment.project))
            .order_by(Experiment.created_at.desc())
        )
        if project_id:
            q = q.where(Experiment.project_id == project_id)
        if status:
            q = q.where(Experiment.status == status)
        if not include_archived:
            q = q.where(Experiment.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, experiment_id: uuid.UUID) -> Experiment:
        """Return experiment by UUID, loading related project and samples."""
        result = await self.db.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.project),
                selectinload(Experiment.samples),
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if experiment is None:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found.")
        return experiment

    async def get_by_code(self, experiment_code: str) -> Experiment | None:
        result = await self.db.execute(
            select(Experiment).where(Experiment.experiment_code == experiment_code)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ExperimentCreate) -> Experiment:
        """Create a new experiment. Validates parent project exists."""
        # Verify parent project exists
        project_service = ProjectService(self.db)
        try:
            await project_service.get_by_id(data.project_id)
        except ProjectNotFoundError:
            raise ProjectNotFoundError(
                f"Cannot create experiment: project {data.project_id} not found."
            )

        # Check code uniqueness
        existing = await self.get_by_code(data.experiment_code)
        if existing is not None:
            raise ExperimentCodeConflictError(
                f"Experiment code '{data.experiment_code}' is already in use."
            )

        experiment = Experiment(
            project_id=data.project_id,
            experiment_code=data.experiment_code,
            title=data.title,
            status=data.status.value,
            experiment_date=data.experiment_date,
            researcher=data.researcher,
            notes=data.notes,
        )
        self.db.add(experiment)
        await self.db.flush()
        await self.db.refresh(experiment)
        logger.info("Experiment created: %s (%s)", experiment.experiment_code, experiment.id)
        return experiment

    async def update(self, experiment_id: uuid.UUID, data: ExperimentUpdate) -> Experiment:
        """Update experiment fields. Only non-None fields are changed."""
        experiment = await self.get_by_id(experiment_id)
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(experiment, field):
                setattr(experiment, field, value.value if hasattr(value, "value") else value)
        await self.db.flush()
        await self.db.refresh(experiment)
        logger.info("Experiment updated: %s", experiment_id)
        return experiment

    async def delete(self, experiment_id: uuid.UUID) -> None:
        """Archive an experiment (soft delete)."""
        experiment = await self.get_by_id(experiment_id)
        experiment.status = "ARCHIVED"
        await self.db.flush()
        logger.info("Experiment archived: %s", experiment_id)

    async def count(
        self,
        project_id: uuid.UUID | None = None,
        include_archived: bool = False,
    ) -> int:
        q = select(func.count(Experiment.id))
        if project_id:
            q = q.where(Experiment.project_id == project_id)
        if not include_archived:
            q = q.where(Experiment.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalar_one()
