"""
GreenSynth Analytics — Dashboard Service

Aggregates counts and summaries for the research dashboard.
All values come from the database — no fabricated data.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.schemas.experiment import ExperimentSummary

logger = logging.getLogger(__name__)


class DashboardService:
    """Provides aggregated statistics for the dashboard page scoped to current project."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self, project_id: uuid.UUID | None = None) -> dict:
        """
        Return dashboard statistics scoped to the given project if provided.
        """
        # Total counts (active only)
        if project_id is not None:
            total_projects = 1
            total_experiments = await self._count_project_experiments(project_id)
            total_samples = await self._count_project_samples(project_id)
            exp_by_status = await self._count_experiments_by_status(project_id)
            proj_by_status = {"ACTIVE": 1}
            recent = await self._recent_experiments(limit=10, project_id=project_id)
        else:
            total_projects = await self._count(Project, exclude_archived=True)
            total_experiments = await self._count(Experiment, exclude_archived=True)
            total_samples = await self._count(Sample, exclude_archived=True)
            exp_by_status = await self._count_experiments_by_status()
            proj_by_status = await self._count_projects_by_status()
            recent = await self._recent_experiments(limit=10)

        return {
            "total_projects": total_projects,
            "total_experiments": total_experiments,
            "total_samples": total_samples,
            "experiments_by_status": exp_by_status,
            "projects_by_status": proj_by_status,
            "recent_experiments": [
                ExperimentSummary.model_validate(e) for e in recent
            ],
        }

    async def _count(self, model, exclude_archived: bool = True) -> int:
        q = select(func.count(model.id))
        if exclude_archived:
            q = q.where(model.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalar_one() or 0

    async def _count_project_experiments(self, project_id: uuid.UUID) -> int:
        q = select(func.count(Experiment.id)).where(
            Experiment.project_id == project_id,
            Experiment.status != "ARCHIVED",
        )
        result = await self.db.execute(q)
        return result.scalar_one() or 0

    async def _count_project_samples(self, project_id: uuid.UUID) -> int:
        q = (
            select(func.count(Sample.id))
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .where(
                Experiment.project_id == project_id,
                Sample.status != "ARCHIVED",
            )
        )
        result = await self.db.execute(q)
        return result.scalar_one() or 0

    async def _count_experiments_by_status(self, project_id: uuid.UUID | None = None) -> dict[str, int]:
        q = (
            select(Experiment.status, func.count(Experiment.id))
            .where(Experiment.status != "ARCHIVED")
        )
        if project_id is not None:
            q = q.where(Experiment.project_id == project_id)
        q = q.group_by(Experiment.status)
        result = await self.db.execute(q)
        return {row[0]: row[1] for row in result.all()}

    async def _count_projects_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Project.status, func.count(Project.id))
            .group_by(Project.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _recent_experiments(self, limit: int = 10, project_id: uuid.UUID | None = None) -> list[Experiment]:
        q = (
            select(Experiment)
            .where(Experiment.status != "ARCHIVED")
        )
        if project_id is not None:
            q = q.where(Experiment.project_id == project_id)
        q = q.order_by(Experiment.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())
