"""
GreenSynth Analytics — Projects API Router

REST endpoints for research project management.
Route handlers are intentionally thin — all logic is in ProjectService.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
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
    db: AsyncSession = Depends(get_db),
) -> list[ProjectSummary]:
    """Return all active research projects."""
    service = ProjectService(db)
    projects = await service.get_all(include_archived=include_archived)
    return [ProjectSummary.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Return a single project by UUID."""
    service = ProjectService(db)
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
    return ProjectResponse.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update an existing project's fields."""
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
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Archive a project (soft delete).

    Projects are archived, not hard-deleted, to preserve
    the scientific data trail.
    """
    service = ProjectService(db)
    try:
        await service.delete(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
