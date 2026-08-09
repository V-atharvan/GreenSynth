"""
GreenSynth Analytics — Project Service

Business logic for project management operations.
Database calls go through SQLAlchemy AsyncSession; no raw SQL here.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found by ID or code."""


class ProjectCodeConflictError(Exception):
    """Raised when a project_code already exists."""


class ProjectService:
    """
    Service layer for project management.

    All database interactions go through this service.
    Route handlers must not contain business logic.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, include_archived: bool = False) -> Sequence[Project]:
        """Return all projects, optionally including archived ones."""
        q = select(Project).order_by(Project.created_at.desc())
        if not include_archived:
            q = q.where(Project.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, project_id: uuid.UUID | str) -> Project:
        """Return a project by UUID, raising ProjectNotFoundError if missing."""
        p_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
        result = await self.db.execute(
            select(Project).where(Project.id == p_uuid)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found.")
        return project

    async def get_by_code(self, project_code: str) -> Project | None:
        """Return a project by project_code, or None."""
        result = await self.db.execute(
            select(Project).where(Project.project_code == project_code)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ProjectCreate) -> Project:
        """Create a new project. Raises ProjectCodeConflictError if code taken."""
        existing = await self.get_by_code(data.project_code)
        if existing is not None:
            raise ProjectCodeConflictError(
                f"Project code '{data.project_code}' is already in use."
            )

        project = Project(
            project_code=data.project_code,
            name=data.name,
            description=data.description,
            material=data.material,
            extract=data.extract,
            solvent=data.solvent,
            synthesis_method=data.synthesis_method,
            status=data.status.value,
        )
        self.db.add(project)
        await self.db.flush()  # Populate id without committing
        await self.db.refresh(project)
        logger.info("Project created: %s (%s)", project.project_code, project.id)
        return project

    async def update(self, project_id: uuid.UUID, data: ProjectUpdate) -> Project:
        """Update project fields. Only non-None fields are changed."""
        project = await self.get_by_id(project_id)
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(project, field):
                # Convert enum value to string for storage
                setattr(project, field, value.value if hasattr(value, "value") else value)
        await self.db.flush()
        await self.db.refresh(project)
        logger.info("Project updated: %s", project_id)
        return project

    async def delete(self, project_id: uuid.UUID) -> None:
        """
        Archive a project (soft delete).

        Projects are archived, not hard-deleted, to preserve
        experimental data traceability.
        """
        project = await self.get_by_id(project_id)
        project.status = "ARCHIVED"
        await self.db.flush()
        logger.info("Project archived: %s", project_id)

    async def count(self, include_archived: bool = False) -> int:
        """Return the total number of projects."""
        q = select(func.count(Project.id))
        if not include_archived:
            q = q.where(Project.status != "ARCHIVED")
        result = await self.db.execute(q)
        return result.scalar_one()
