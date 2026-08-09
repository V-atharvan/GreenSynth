"""
GreenSynth Analytics — Parameters API Router

REST API endpoints for parameter definitions and recorded experiment parameters.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.parameter import (
    BatchExperimentParametersInput,
    ExperimentParameterCreate,
    ExperimentParameterResponse,
    ParameterDefinitionCreate,
    ParameterDefinitionResponse,
    ParameterDefinitionUpdate,
)
from app.services.parameter_service import (
    ParameterNotFoundError,
    ParameterService,
    ParameterValidationError,
)

router = APIRouter(tags=["parameters"])


# ── Project Parameter Definitions ───────────────────────────

@router.get(
    "/projects/{project_id}/parameters",
    response_model=list[ParameterDefinitionResponse],
    summary="Get project parameter definitions",
)
async def get_project_parameters(
    project_id: uuid.UUID,
    include_inactive: bool = Query(default=False, description="Include inactive parameter definitions"),
    db: AsyncSession = Depends(get_db),
) -> list[ParameterDefinitionResponse]:
    """Return synthesis parameter definitions configured for a project."""
    service = ParameterService(db)
    definitions = await service.get_project_definitions(
        project_id, active_only=not include_inactive
    )
    return [ParameterDefinitionResponse.model_validate(p) for p in definitions]


@router.post(
    "/projects/{project_id}/parameters",
    response_model=ParameterDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new parameter definition to a project",
)
async def create_project_parameter(
    project_id: uuid.UUID,
    data: ParameterDefinitionCreate,
    db: AsyncSession = Depends(get_db),
) -> ParameterDefinitionResponse:
    """Define a new synthesis parameter for a project."""
    service = ParameterService(db)
    pdef = await service.create_definition(project_id, data)
    return ParameterDefinitionResponse.model_validate(pdef)


@router.put(
    "/projects/{project_id}/parameters/{parameter_id}",
    response_model=ParameterDefinitionResponse,
    summary="Update a parameter definition",
)
async def update_project_parameter(
    project_id: uuid.UUID,
    parameter_id: uuid.UUID,
    data: ParameterDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
) -> ParameterDefinitionResponse:
    """Update constraints, description, or status of a parameter definition."""
    service = ParameterService(db)
    try:
        pdef = await service.update_definition(parameter_id, data)
    except ParameterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ParameterDefinitionResponse.model_validate(pdef)


@router.delete(
    "/projects/{project_id}/parameters/{parameter_id}",
    response_model=ParameterDefinitionResponse,
    summary="Deactivate a parameter definition",
)
async def deactivate_project_parameter(
    project_id: uuid.UUID,
    parameter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ParameterDefinitionResponse:
    """
    Deactivate a parameter definition.

    Marks parameter status INACTIVE to preserve historical experiment integrity.
    """
    service = ParameterService(db)
    try:
        pdef = await service.deactivate_definition(parameter_id)
    except ParameterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ParameterDefinitionResponse.model_validate(pdef)


# ── Experiment Parameter Values ─────────────────────────────

@router.get(
    "/experiments/{experiment_id}/parameters",
    response_model=list[ExperimentParameterResponse],
    summary="Get recorded parameters for an experiment",
)
async def get_experiment_parameters(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentParameterResponse]:
    """Return recorded synthesis parameters for an experiment."""
    service = ParameterService(db)
    params = await service.get_experiment_parameters(experiment_id)
    return [ExperimentParameterResponse.model_validate(p) for p in params]


@router.post(
    "/experiments/{experiment_id}/parameters",
    response_model=list[ExperimentParameterResponse],
    summary="Save synthesis parameters for an experiment",
)
async def save_experiment_parameters(
    experiment_id: uuid.UUID,
    payload: BatchExperimentParametersInput,
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentParameterResponse]:
    """
    Save or update synthesis parameters for an experiment.

    Validates all values against project parameter definitions.
    Raises 422 Unprocessable Entity if required parameters are missing or values are out of bounds.
    """
    service = ParameterService(db)
    try:
        saved = await service.save_experiment_parameters(experiment_id, payload.parameters)
    except ParameterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ParameterValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return [ExperimentParameterResponse.model_validate(p) for p in saved]
