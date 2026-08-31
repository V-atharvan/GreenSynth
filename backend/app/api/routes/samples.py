"""
GreenSynth Analytics — Samples API Router

REST API endpoints for physical samples with authorization & project isolation.
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
from app.schemas.sample import SampleCreate, SampleResponse, SampleSummary, SampleUpdate
from app.services.experiment_service import ExperimentNotFoundError, ExperimentService
from app.services.sample_service import (
    SampleCodeConflictError,
    SampleNotFoundError,
    SampleService,
)

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get(
    "/",
    response_model=list[SampleSummary],
    summary="List samples",
)
async def list_samples(
    project_id: uuid.UUID | None = Query(default=None, description="Filter by project"),
    experiment_id: uuid.UUID | None = Query(default=None, description="Filter by experiment"),
    status: str | None = Query(default=None, description="Filter by status"),
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SampleSummary]:
    """Return samples belonging to the authenticated user's authorized scope."""
    service = SampleService(db)

    if current_user.is_admin:
        samples = await service.get_all(
            experiment_id=experiment_id,
            status=status,
            include_archived=include_archived,
            project_id=project_id,
        )
        return [SampleSummary.model_validate(s) for s in samples]

    # Student user
    current_project = await get_current_project(current_user=current_user, db=db)
    if project_id is not None:
        verify_project_access(project_id, current_project, current_user)

    if experiment_id is not None:
        exp_service = ExperimentService(db)
        try:
            exp = await exp_service.get_by_id(experiment_id)
            if exp.project_id != current_project.id:
                return []
        except ExperimentNotFoundError:
            return []

    samples = await service.get_all(
        experiment_id=experiment_id,
        status=status,
        include_archived=include_archived,
        project_id=current_project.id,
    )
    return [SampleSummary.model_validate(s) for s in samples]


@router.get(
    "/{sample_id}",
    response_model=SampleResponse,
    summary="Get a sample by ID",
)
async def get_sample(
    sample_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Return a single sample by UUID with IDOR verification."""
    service = SampleService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        sample = await service.get_by_id(sample_id, project_id=target_project_id)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SampleResponse.model_validate(sample)


@router.post(
    "/",
    response_model=SampleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sample",
)
async def create_sample(
    data: SampleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Create a new sample linked to an authorized experiment."""
    exp_service = ExperimentService(db)
    try:
        exp = await exp_service.get_by_id(data.experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not current_user.is_admin:
        auth_project_ids = await get_authorized_project_ids(current_user, db)
        if exp.project_id not in auth_project_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{data.experiment_id}' not found.",
            )

    service = SampleService(db)
    try:
        sample = await service.create(data)
    except SampleCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SampleResponse.model_validate(sample)


@router.put(
    "/{sample_id}",
    response_model=SampleResponse,
    summary="Update a sample",
)
async def update_sample(
    sample_id: uuid.UUID,
    data: SampleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Update an existing sample's fields with IDOR verification."""
    service = SampleService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        await service.get_by_id(sample_id, project_id=target_project_id)
        sample = await service.update(sample_id, data)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SampleResponse.model_validate(sample)


@router.delete(
    "/{sample_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a sample",
)
async def delete_sample(
    sample_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Archive a sample (soft delete) with IDOR verification."""
    service = SampleService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        await service.get_by_id(sample_id, project_id=target_project_id)
        await service.delete(sample_id)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
