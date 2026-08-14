"""
GreenSynth Analytics — Experiments API Router
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
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
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentSummary]:
    """Return experiments, optionally filtered by project or status."""
    service = ExperimentService(db)
    experiments = await service.get_all(
        project_id=project_id,
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
    db: AsyncSession = Depends(get_db),
) -> ExperimentWithProject:
    """Return a single experiment with its parent project details."""
    service = ExperimentService(db)
    try:
        experiment = await service.get_by_id(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ExperimentWithProject.model_validate(experiment)


@router.post(
    "/",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new experiment",
)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Create a new experiment under an existing project."""
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
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Update an existing experiment's fields."""
    service = ExperimentService(db)
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
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete an experiment and all dependent records."""
    service = ExperimentService(db)
    try:
        await service.delete(experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
