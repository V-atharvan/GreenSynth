"""
GreenSynth Analytics — Analytics & Sample Comparison REST API Endpoints

Provides endpoints for creating, listing, querying, comparing, and exporting analytics datasets with authorization.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.statistics.correlation import CorrelationError
from app.analytics.statistics.regression import RegressionError
from app.analytics.statistics.schemas import (
    ComparisonTableResponse,
    DatasetCreateInput,
    DatasetResponse,
    StatisticalAnalysisResponse,
    StatisticalAnalysisRunInput,
)
from app.analytics.statistics.service import AnalyticsService
from app.api.deps import (
    get_authorized_project_ids,
    get_current_project,
    get_current_user,
    get_db,
    verify_project_access,
)
from app.models.project import Project
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post(
    "/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a logical comparison dataset",
)
async def create_comparison_dataset(
    payload: DatasetCreateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Create a comparison dataset referencing selected project samples and variables."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(payload.project_id, current_project, current_user)

    service = AnalyticsService(db)
    try:
        ds = await service.create_dataset(payload)
        return DatasetResponse.model_validate(ds)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/datasets",
    response_model=list[DatasetResponse],
    summary="List comparison datasets for a project",
)
async def list_comparison_datasets(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DatasetResponse]:
    """List datasets for the authorized project."""
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        verify_project_access(project_id, current_project, current_user)

    service = AnalyticsService(db)
    datasets = await service.list_datasets_for_project(project_id)
    return [DatasetResponse.model_validate(ds) for ds in datasets]


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get comparison dataset details",
)
async def get_comparison_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Get dataset definition with IDOR protection."""
    service = AnalyticsService(db)
    try:
        ds = await service.get_dataset(dataset_id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if ds.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return DatasetResponse.model_validate(ds)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/datasets/{dataset_id}/comparison-table",
    response_model=ComparisonTableResponse,
    summary="Get multi-sample comparison table with data status provenance",
)
async def get_dataset_comparison_table(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonTableResponse:
    """Get provenance-aware multi-sample comparison table with IDOR protection."""
    service = AnalyticsService(db)
    try:
        ds = await service.get_dataset(dataset_id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if ds.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return await service.build_comparison_table(dataset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/datasets/{dataset_id}/statistics",
    response_model=StatisticalAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run statistical analysis on a comparison dataset",
)
async def run_dataset_statistical_analysis(
    dataset_id: uuid.UUID,
    payload: StatisticalAnalysisRunInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatisticalAnalysisResponse:
    """Execute statistical analysis (DESCRIPTIVE, CORRELATION, REGRESSION, GROUP_COMPARISON, OUTLIERS) with IDOR protection."""
    service = AnalyticsService(db)
    try:
        ds = await service.get_dataset(dataset_id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if ds.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        stat = await service.run_statistical_analysis(dataset_id, payload)
        return StatisticalAnalysisResponse.model_validate(stat)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (CorrelationError, RegressionError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/statistical-analyses/{analysis_id}",
    response_model=StatisticalAnalysisResponse,
    summary="Get statistical analysis result",
)
async def get_statistical_analysis_result(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatisticalAnalysisResponse:
    """Get statistical analysis record by ID with IDOR protection."""
    service = AnalyticsService(db)
    try:
        stat = await service.get_statistical_analysis(analysis_id)
        ds = await service.get_dataset(stat.dataset_id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if ds.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
        return StatisticalAnalysisResponse.model_validate(stat)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/datasets/{dataset_id}/export",
    summary="Export comparison dataset table to CSV",
)
async def export_dataset_csv(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export comparison dataset table to CSV file download with IDOR protection."""
    service = AnalyticsService(db)
    try:
        ds = await service.get_dataset(dataset_id)
        if not current_user.is_admin:
            auth_ids = await get_authorized_project_ids(current_user, db)
            if ds.project_id not in auth_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        csv_str = await service.export_dataset_csv(dataset_id)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="comparison_dataset_{dataset_id!s}.csv"'},
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
