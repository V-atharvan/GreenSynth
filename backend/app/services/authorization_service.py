"""
GreenSynth Analytics — Centralized Authorization Service

Provides reusable authorization verification for:
1. Resolving student active group membership.
2. Resolving student assigned synthesis project.
3. Enforcing project-level and resource-level access control.
4. Bypassing project restrictions for System Administrators.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User


class AuthorizationService:
    """Centralized authorization resolution and validation service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_authorized_project_ids(self, user: User) -> list[uuid.UUID]:
        """
        Returns list of authorized project UUIDs:
        - Admin: All active projects.
        - Student: Projects belonging to the student's active research groups.
        """
        if user.is_admin:
            res = await self.db.execute(
                select(Project.id).where(Project.status == ProjectStatus.ACTIVE.value)
            )
            return list(res.scalars().all())

        q = (
            select(ResearchGroup.project_id)
            .join(GroupMembership, GroupMembership.group_id == ResearchGroup.id)
            .where(
                GroupMembership.user_id == user.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
                ResearchGroup.status == GroupStatus.ACTIVE.value,
            )
        )
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def resolve_student_project(self, user: User) -> Project:
        """
        Resolves the authorized Project entity for a Student.
        Raises 403 Forbidden if the student has no active group membership.
        """
        if user.is_admin:
            res = await self.db.execute(
                select(Project)
                .where(Project.status == ProjectStatus.ACTIVE.value)
                .order_by(Project.project_code.asc())
            )
            projects = res.scalars().all()
            p7 = next((p for p in projects if p.project_code == "P7"), None)
            if p7:
                return p7
            if projects:
                return projects[0]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NO_PROJECTS", "message": "No active projects exist in catalog."},
            )

        q = (
            select(Project)
            .join(ResearchGroup, ResearchGroup.project_id == Project.id)
            .join(GroupMembership, GroupMembership.group_id == ResearchGroup.id)
            .where(
                GroupMembership.user_id == user.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
                ResearchGroup.status == GroupStatus.ACTIVE.value,
                Project.status == ProjectStatus.ACTIVE.value,
            )
        )
        res = await self.db.execute(q)
        project = res.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "NO_ACTIVE_GROUP",
                    "message": "User is not assigned to an active research group.",
                },
            )
        return project

    async def resolve_student_group(self, user: User) -> ResearchGroup:
        """
        Resolves the active ResearchGroup entity for a Student.
        """
        q = (
            select(ResearchGroup)
            .join(GroupMembership, GroupMembership.group_id == ResearchGroup.id)
            .where(
                GroupMembership.user_id == user.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
                ResearchGroup.status == GroupStatus.ACTIVE.value,
            )
        )
        res = await self.db.execute(q)
        group = res.scalar_one_or_none()
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "NO_ACTIVE_GROUP",
                    "message": "User is not assigned to an active research group.",
                },
            )
        return group

    async def check_project_access(self, user: User, project_id: uuid.UUID) -> bool:
        """
        Validates if user has authorization to access the specified project_id.
        """
        if user.is_admin:
            return True
        authorized_ids = await self.get_authorized_project_ids(user)
        return project_id in authorized_ids

    async def verify_project_access(self, user: User, project_id: uuid.UUID) -> None:
        """
        Enforces project authorization. Raises 403 Forbidden on access denial.
        """
        allowed = await self.check_project_access(user, project_id)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PROJECT_ACCESS_DENIED",
                    "message": "You do not have access to this project.",
                },
            )
