"""
GreenSynth Analytics — Samples API Router
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.sample import SampleCreate, SampleResponse, SampleSummary, SampleUpdate
from app.services.experiment_service import ExperimentNotFoundError
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
    experiment_id: uuid.UUID | None = Query(default=None, description="Filter by experiment"),
    status: str | None = Query(default=None, description="Filter by status"),
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[SampleSummary]:
    """Return samples, optionally filtered by experiment or status."""
    service = SampleService(db)
    samples = await service.get_all(
        experiment_id=experiment_id,
        status=status,
        include_archived=include_archived,
    )
    return [SampleSummary.model_validate(s) for s in samples]


@router.get(
    "/{sample_id}",
    response_model=SampleResponse,
    summary="Get a sample by ID",
)
async def get_sample(
    sample_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Return a single sample by UUID."""
    service = SampleService(db)
    try:
        sample = await service.get_by_id(sample_id)
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
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Create a new sample linked to an experiment."""
    service = SampleService(db)
    try:
        sample = await service.create(data)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
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
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Update an existing sample's fields."""
    service = SampleService(db)
    try:
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
    db: AsyncSession = Depends(get_db),
) -> None:
    """Archive a sample (soft delete)."""
    service = SampleService(db)
    try:
        await service.delete(sample_id)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
