"""
GreenSynth Analytics — Projects API Router

REST endpoints for research project management.
Admin users have system-wide visibility (P1–P8); Student users see only their authorized project.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_project,
    get_current_user,
    get_db,
    verify_project_access,
)
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project
from app.models.research_group import ResearchGroup
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary, ProjectUpdate
from app.services.project_service import (
    ProjectCodeConflictError,
    ProjectNotFoundError,
    ProjectService,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "/",
    response_model=list[ProjectSummary],
    summary="List all research projects",
)
async def list_projects(
    include_archived: bool = Query(default=False, description="Include archived projects"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectSummary]:
    """
    Return research projects based on user authorization.
    - Admin: Returns all active research projects (P1 through P8).
    - Student: Returns only the student's authorized project.
    """
    service = ProjectService(db)

    if current_user.is_admin:
        projects = await service.get_all(include_archived=include_archived)
        return [ProjectSummary.model_validate(p) for p in projects]

    # Student user
    current_project = await get_current_project(current_user=current_user, db=db)
    if current_project.status == "ARCHIVED" and not include_archived:
        return []
    return [ProjectSummary.model_validate(current_project)]


@router.get(
    "/catalog",
    response_model=list[ProjectSummary],
    summary="List all active research projects in public catalog",
)
async def get_project_catalog(
    db: AsyncSession = Depends(get_db),
) -> list[ProjectSummary]:
    """
    Return public read-only catalog of all active research projects (P1–P8).
    Used for research group registration and public catalog viewing.
    No authentication required.
    """
    service = ProjectService(db)
    projects = await service.get_all(include_archived=False)
    sorted_projects = sorted(
        projects,
        key=lambda p: (
            int(p.project_code[1:]) if p.project_code.startswith("P") and p.project_code[1:].isdigit() else 999,
            p.project_code,
        ),
    )
    return [ProjectSummary.model_validate(p) for p in sorted_projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Return a single project by UUID for authorized user."""
    service = ProjectService(db)

    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(project_id, current_project, current_user)

    try:
        project = await service.get_by_id(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ProjectResponse.model_validate(project)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new research project",
)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new research project."""
    service = ProjectService(db)
    try:
        project = await service.create(data)
    except ProjectCodeConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    # If student leader created it, link with their group
    if not current_user.is_admin:
        mem_res = await db.execute(
            select(GroupMembership).where(
                GroupMembership.user_id == current_user.id,
                GroupMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        membership = mem_res.scalar_one_or_none()
        if membership:
            stmt = select(ResearchGroup).where(ResearchGroup.id == membership.group_id)
            res = await db.execute(stmt)
            group = res.scalar_one_or_none()
            if group:
                group.project_id = project.id
                await db.commit()

    return ProjectResponse.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update an existing project's fields."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(project_id, current_project, current_user)

    service = ProjectService(db)
    try:
        project = await service.update(project_id, data)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a project",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Archive a project (soft delete).
    Projects are archived, not hard-deleted, to preserve the scientific data trail.
    """
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(project_id, current_project, current_user)

    service = ProjectService(db)
    try:
        await service.delete(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
