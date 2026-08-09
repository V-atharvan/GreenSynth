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
    """Provides aggregated statistics for the dashboard page."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self) -> dict:
        """
        Return dashboard statistics.

        Returns only real database values — no hard-coded or
        fabricated counts.
        """
        # Total counts (active only)
        total_projects = await self._count(Project, exclude_archived=True)
        total_experiments = await self._count(Experiment, exclude_archived=True)
        total_samples = await self._count(Sample, exclude_archived=True)

        # Experiments by status
        exp_by_status = await self._count_experiments_by_status()

        # Projects by status
        proj_by_status = await self._count_projects_by_status()

        # Recent experiments (last 10)
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

    async def _count_experiments_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Experiment.status, func.count(Experiment.id))
            .where(Experiment.status != "ARCHIVED")
            .group_by(Experiment.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _count_projects_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Project.status, func.count(Project.id))
            .group_by(Project.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _recent_experiments(self, limit: int = 10) -> list[Experiment]:
        result = await self.db.execute(
            select(Experiment)
            .where(Experiment.status != "ARCHIVED")
            .order_by(Experiment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
