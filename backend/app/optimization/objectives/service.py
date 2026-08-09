"""
GreenSynth Analytics — Objective Service Layer

Manages research objective creation, scientific validation, activation, versioning (v1 -> v2), and audit logging.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doe import Objective
from app.models.project import Project
from app.optimization.objectives.schemas import ObjectiveCreateInput
from app.optimization.objectives.validation import validate_objective_definition
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ObjectiveService:
    """Service layer for optimization objective management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def create_objective(
        self, payload: ObjectiveCreateInput, created_by: str | None = None
    ) -> Objective:
        """Validate and create a draft objective."""
        validate_objective_definition(payload)

        # Check project exists
        from app.services.project_service import ProjectNotFoundError, ProjectService
        try:
            await ProjectService(self.db).get_by_id(payload.project_id)
        except ProjectNotFoundError as exc:
            all_p = await ProjectService(self.db).get_all(include_archived=True)
            logger.error("Project lookup failed. Target: %s, Existing in DB: %s", payload.project_id, [str(p.id) for p in all_p])
            raise ValueError(str(exc)) from exc

        obj = Objective(
            project_id=payload.project_id,
            name=payload.name,
            version="v1",
            description=payload.description,
            target_property=payload.target_property,
            direction=payload.direction.upper(),
            target_value=payload.target_value,
            min_value=payload.min_value,
            max_value=payload.max_value,
            unit=payload.unit,
            weight=payload.weight,
            synthesis_method=payload.synthesis_method,
            solvent=payload.solvent,
            constraints=[c.model_dump() for c in payload.constraints] if payload.constraints else None,
            status="DRAFT",
            created_by=created_by,
        )
        self.db.add(obj)
        await self.db.flush()

        await self.audit.log(
            entity_type="Objective",
            entity_id=obj.id,
            action="CREATE_OBJECTIVE",
            changes={"name": obj.name, "target_property": obj.target_property, "direction": obj.direction},
        )
        return obj

    async def get_objective(self, objective_id: uuid.UUID) -> Objective:
        """Fetch objective by ID or raise error."""
        res = await self.db.execute(select(Objective).where(Objective.id == objective_id))
        obj = res.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"Objective {objective_id} not found.")
        return obj

    async def list_project_objectives(self, project_id: uuid.UUID) -> Sequence[Objective]:
        """List objectives for a project."""
        res = await self.db.execute(
            select(Objective)
            .where(Objective.project_id == project_id)
            .order_by(Objective.created_at.desc())
        )
        return res.scalars().all()

    async def activate_objective(self, objective_id: uuid.UUID) -> Objective:
        """Validate and activate objective (DRAFT -> ACTIVE)."""
        obj = await self.get_objective(objective_id)
        if obj.status == "ACTIVE":
            return obj

        # Re-validate
        validate_objective_definition(
            ObjectiveCreateInput(
                project_id=obj.project_id,
                name=obj.name,
                target_property=obj.target_property,
                direction=obj.direction,
                target_value=obj.target_value,
                min_value=obj.min_value,
                max_value=obj.max_value,
                unit=obj.unit,
                weight=obj.weight,
            )
        )
        obj.status = "ACTIVE"
        await self.db.flush()

        await self.audit.log(
            entity_type="Objective",
            entity_id=obj.id,
            action="ACTIVATE_OBJECTIVE",
            changes={"status": "ACTIVE"},
        )
        return obj

    async def archive_objective(self, objective_id: uuid.UUID) -> Objective:
        """Archive objective."""
        obj = await self.get_objective(objective_id)
        obj.status = "ARCHIVED"
        await self.db.flush()

        await self.audit.log(
            entity_type="Objective",
            entity_id=obj.id,
            action="ARCHIVE_OBJECTIVE",
            changes={"status": "ARCHIVED"},
        )
        return obj

    async def create_new_version(
        self, objective_id: uuid.UUID, payload: ObjectiveCreateInput, created_by: str | None = None
    ) -> Objective:
        """Create new version (v2, v3) of an existing objective while leaving previous version unchanged."""
        parent_obj = await self.get_objective(objective_id)
        validate_objective_definition(payload)

        # Parse current version number (v1 -> v2)
        v_num = 1
        if parent_obj.version.startswith("v"):
            try:
                v_num = int(parent_obj.version[1:]) + 1
            except ValueError:
                v_num = 2

        new_obj = Objective(
            project_id=payload.project_id,
            name=payload.name,
            version=f"v{v_num}",
            description=payload.description,
            target_property=payload.target_property,
            direction=payload.direction.upper(),
            target_value=payload.target_value,
            min_value=payload.min_value,
            max_value=payload.max_value,
            unit=payload.unit,
            weight=payload.weight,
            synthesis_method=payload.synthesis_method,
            solvent=payload.solvent,
            constraints=[c.model_dump() for c in payload.constraints] if payload.constraints else None,
            status="DRAFT",
            created_by=created_by,
        )
        self.db.add(new_obj)
        await self.db.flush()

        await self.audit.log(
            entity_type="Objective",
            entity_id=new_obj.id,
            action="CREATE_OBJECTIVE_VERSION",
            changes={"version": new_obj.version, "parent_id": str(parent_obj.id)},
        )
        return new_obj
