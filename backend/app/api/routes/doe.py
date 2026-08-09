"""
GreenSynth Analytics — Design of Experiments (DOE) REST API Router (Phase 14 Extended)
"""

from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.optimization.doe.schemas import (
    DOEAnalysisResponse,
    DOECreateInput,
    DOEQualityReport,
    DOEResponse,
    DOEWorkloadPreview,
    ProposedExperimentResponse,
)
from app.optimization.doe.service import DOEService
from app.optimization.objectives.schemas import ObjectiveCreateInput, ObjectiveResponse
from app.optimization.objectives.service import ObjectiveService
from app.schemas.experiment import ExperimentResponse

router = APIRouter()


# ── OBJECTIVE ENDPOINTS ───────────────────────────────────────

@router.post(
    "/objectives",
    response_model=ObjectiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft optimization objective",
)
async def create_objective(
    payload: ObjectiveCreateInput,
    db: AsyncSession = Depends(get_db),
) -> ObjectiveResponse:
    """Formally define an optimization objective (MAXIMIZE, MINIMIZE, TARGET_VALUE, TARGET_RANGE)."""
    service = ObjectiveService(db)
    try:
        obj = await service.create_objective(payload)
        return ObjectiveResponse.model_validate(obj)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/objectives",
    response_model=list[ObjectiveResponse],
    summary="List project optimization objectives",
)
async def list_objectives(
    project_id: uuid.UUID = Query(..., description="Project ID filter"),
    db: AsyncSession = Depends(get_db),
) -> list[ObjectiveResponse]:
    """List optimization objectives defined for a project."""
    service = ObjectiveService(db)
    objs = await service.list_project_objectives(project_id)
    return [ObjectiveResponse.model_validate(o) for o in objs]


@router.get(
    "/objectives/{objective_id}",
    response_model=ObjectiveResponse,
    summary="Get objective definition details",
)
async def get_objective(
    objective_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ObjectiveResponse:
    """Fetch objective definition by ID."""
    service = ObjectiveService(db)
    try:
        obj = await service.get_objective(objective_id)
        return ObjectiveResponse.model_validate(obj)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/objectives/{objective_id}/activate",
    response_model=ObjectiveResponse,
    summary="Activate objective definition",
)
async def activate_objective(
    objective_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ObjectiveResponse:
    """Validate and transition draft objective to ACTIVE status."""
    service = ObjectiveService(db)
    try:
        obj = await service.activate_objective(objective_id)
        return ObjectiveResponse.model_validate(obj)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ── DOE STUDY ENDPOINTS ───────────────────────────────────────

@router.post(
    "/doe/preview",
    response_model=DOEWorkloadPreview,
    summary="Preview DOE workload and run count",
)
async def preview_doe_workload(
    payload: DOECreateInput,
    db: AsyncSession = Depends(get_db),
) -> DOEWorkloadPreview:
    """Calculates expected run count preview and displays workload warning if runs exceed threshold."""
    service = DOEService(db)
    try:
        return await service.preview_workload(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/doe",
    status_code=status.HTTP_201_CREATED,
    summary="Create DOE and generate proposed experiments",
)
async def create_doe_and_generate(
    payload: DOECreateInput,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create Design of Experiments study and generate proposed experiment conditions."""
    service = DOEService(db)
    try:
        doe, report = await service.create_doe_and_generate(payload)
        return {
            "doe": DOEResponse.model_validate(doe),
            "quality_report": report,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/doe",
    response_model=list[DOEResponse],
    summary="List project DOE studies",
)
async def list_project_does(
    project_id: uuid.UUID = Query(..., description="Project ID filter"),
    db: AsyncSession = Depends(get_db),
) -> list[DOEResponse]:
    """Fetch all DOE studies defined for a project."""
    service = DOEService(db)
    does = await service.list_project_does(project_id)
    return [DOEResponse.model_validate(d) for d in does]


@router.get(
    "/doe/{doe_id}",
    response_model=DOEResponse,
    summary="Get DOE study details",
)
async def get_doe(
    doe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DOEResponse:
    """Fetch DOE configuration by ID."""
    service = DOEService(db)
    try:
        doe = await service.get_doe(doe_id)
        return DOEResponse.model_validate(doe)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/doe/{doe_id}/approve",
    response_model=DOEResponse,
    summary="Approve DOE study and lock version V1",
)
async def approve_doe_study(
    doe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DOEResponse:
    """Approve DOE study and lock version V1 as immutable."""
    service = DOEService(db)
    try:
        doe = await service.approve_doe_study(doe_id)
        return DOEResponse.model_validate(doe)
    except ValueError as exc:
        logger.error(f"Error approving DOE study {doe_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/doe/{doe_id}/regenerate",
    status_code=status.HTTP_201_CREATED,
    summary="Create DOE version V2 and regenerate design matrix",
)
async def regenerate_doe_version(
    doe_id: uuid.UUID,
    payload: DOECreateInput,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create new DOE version (e.g. v2.0) maintaining previous version immutability."""
    service = DOEService(db)
    try:
        new_doe, report = await service.regenerate_doe_version(doe_id, payload)
        return {
            "doe": DOEResponse.model_validate(new_doe),
            "quality_report": report,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/doe/{doe_id}/proposed-experiments",
    response_model=list[ProposedExperimentResponse],
    summary="List DOE proposed experiment runs",
)
async def list_proposed_experiments(
    doe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ProposedExperimentResponse]:
    """Fetch generated proposed experiment runs for a DOE study."""
    service = DOEService(db)
    proposed = await service.list_proposed_experiments(doe_id)
    return [ProposedExperimentResponse.model_validate(p) for p in proposed]


@router.post(
    "/doe/proposed-experiments/{proposed_id}/convert",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convert approved proposed experiment into a PLANNED experiment",
)
async def convert_to_planned_experiment(
    proposed_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Convert approved proposed experiment condition into a real PLANNED experiment."""
    service = DOEService(db)
    try:
        exp = await service.convert_run_to_planned_experiment(proposed_id)
        return ExperimentResponse.model_validate(exp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/doe/{doe_id}/analysis",
    response_model=DOEAnalysisResponse,
    summary="Get DOE statistical effects and response surface fit",
)
async def analyze_doe(
    doe_id: uuid.UUID,
    response_property: str = Query(default="Electrical Conductivity", description="Target response property"),
    db: AsyncSession = Depends(get_db),
) -> DOEAnalysisResponse:
    """Compute Main Effects, Interaction Effects, and Response Surface model fit."""
    service = DOEService(db)
    try:
        analysis = await service.analyze_doe(doe_id, response_property=response_property)
        return DOEAnalysisResponse.model_validate(analysis)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/doe/{doe_id}/export",
    summary="Export DOE proposed design matrix to CSV",
)
async def export_doe_csv(
    doe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export proposed experiments design matrix to CSV file."""
    service = DOEService(db)
    csv_content = await service.export_doe_csv(doe_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=doe_{doe_id}_design.csv"},
    )
