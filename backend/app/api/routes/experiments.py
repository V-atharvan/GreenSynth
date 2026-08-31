"""
GreenSynth Analytics — Experiments API Router

REST API endpoints for experiment management with full authorization & project isolation.
Admin users have system-wide access; Student users are strictly scoped to their authorized project.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_authorized_project_ids,
    get_current_project,
    get_current_user,
    get_db,
    verify_project_access,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentSummary,
    ExperimentUpdate,
    ExperimentWithProject,
)
from app.services.experiment_service import (
    ExperimentCodeConflictError,
    ExperimentNotFoundError,
    ExperimentService,
)
from app.services.project_service import ProjectNotFoundError

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get(
    "/",
    response_model=list[ExperimentSummary],
    summary="List experiments",
)
async def list_experiments(
    project_id: uuid.UUID | None = Query(default=None, description="Filter by project"),
    status: str | None = Query(default=None, description="Filter by status"),
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentSummary]:
    """Return experiments for the authenticated user's authorized scope."""
    service = ExperimentService(db)

    if current_user.is_admin:
        experiments = await service.get_all(
            project_id=project_id,
            status=status,
            include_archived=include_archived,
        )
        return [ExperimentSummary.model_validate(e) for e in experiments]

    # Student user
    current_project = await get_current_project(current_user=current_user, db=db)
    if project_id is not None:
        verify_project_access(project_id, current_project, current_user)

    experiments = await service.get_all(
        project_id=current_project.id,
        status=status,
        include_archived=include_archived,
    )
    return [ExperimentSummary.model_validate(e) for e in experiments]


@router.get(
    "/{experiment_id}",
    response_model=ExperimentWithProject,
    summary="Get an experiment by ID",
)
async def get_experiment(
    experiment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentWithProject:
    """Return a single experiment with IDOR protection."""
    service = ExperimentService(db)
    try:
        experiment = await service.get_by_id(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not current_user.is_admin:
        auth_project_ids = await get_authorized_project_ids(current_user, db)
        if experiment.project_id not in auth_project_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found.",
            )

    return ExperimentWithProject.model_validate(experiment)


@router.post(
    "/",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new experiment",
)
async def create_experiment(
    data: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Create a new experiment under the authorized project."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        if data.project_id is not None:
            verify_project_access(data.project_id, current_project, current_user)
        else:
            data.project_id = current_project.id
    else:
        if data.project_id is None:
            # Fallback to default active project for admin
            current_project = await get_current_project(current_user=current_user, db=db)
            data.project_id = current_project.id

    service = ExperimentService(db)
    try:
        experiment = await service.create(data)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ExperimentCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ExperimentResponse.model_validate(experiment)


@router.put(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Update an experiment",
)
async def update_experiment(
    experiment_id: uuid.UUID,
    data: ExperimentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Update an existing experiment's fields with IDOR protection."""
    service = ExperimentService(db)
    try:
        existing = await service.get_by_id(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not current_user.is_admin:
        auth_project_ids = await get_authorized_project_ids(current_user, db)
        if existing.project_id not in auth_project_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found.",
            )

    try:
        experiment = await service.update(experiment_id, data)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ExperimentResponse.model_validate(experiment)


@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an experiment",
)
async def delete_experiment(
    experiment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete an experiment and all dependent records with IDOR protection."""
    service = ExperimentService(db)
    try:
        existing = await service.get_by_id(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not current_user.is_admin:
        auth_project_ids = await get_authorized_project_ids(current_user, db)
        if existing.project_id not in auth_project_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' not found.",
            )

    try:
        await service.delete(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
