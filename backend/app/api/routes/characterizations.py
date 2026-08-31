"""
GreenSynth Analytics — Characterizations API Router

REST API endpoints for laboratory characterizations and raw file uploads with authorization & project isolation.
"""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project, get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.characterization import (
    CharacterizationCreate,
    CharacterizationResponse,
    RawFileResponse,
)
from app.services.characterization_service import (
    CharacterizationNotFoundError,
    CharacterizationService,
    DuplicateFileError,
    FileSizeExceededValidationError,
    InvalidFileTypeValidationError,
)
from app.services.sample_service import SampleNotFoundError, SampleService

router = APIRouter(tags=["characterizations"])


@router.post(
    "/characterizations",
    response_model=CharacterizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create characterization run metadata",
)
async def create_characterization(
    data: CharacterizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterizationResponse:
    """Create a new laboratory characterization run for an authorized sample."""
    sample_service = SampleService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        await sample_service.get_by_id(data.sample_id, project_id=target_project_id)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    service = CharacterizationService(db)
    try:
        ch = await service.create_characterization(data)
    except SampleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return CharacterizationResponse.model_validate(ch)


@router.get(
    "/characterizations/{characterization_id}",
    response_model=CharacterizationResponse,
    summary="Get characterization run details",
)
async def get_characterization(
    characterization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterizationResponse:
    """Get single characterization record with IDOR verification."""
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        ch = await service.get_by_id(characterization_id, project_id=target_project_id)
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return CharacterizationResponse.model_validate(ch)


@router.get(
    "/samples/{sample_id}/characterizations",
    response_model=list[CharacterizationResponse],
    summary="List characterizations for a sample",
)
async def list_sample_characterizations(
    sample_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CharacterizationResponse]:
    """Return all characterization runs linked to an authorized physical sample."""
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    chs = await service.list_sample_characterizations(sample_id, project_id=target_project_id)
    return [CharacterizationResponse.model_validate(c) for c in chs]


@router.post(
    "/characterizations/{characterization_id}/files",
    response_model=RawFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a raw laboratory file",
)
async def upload_raw_file(
    characterization_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RawFileResponse:
    """
    Upload an immutable raw laboratory data file for an authorized characterization run.
    """
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        await service.get_by_id(characterization_id, project_id=target_project_id)
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    file_bytes = await file.read()
    original_filename = file.filename or "uploaded_file"

    try:
        raw_file = await service.upload_raw_file(
            characterization_id=characterization_id,
            file_bytes=file_bytes,
            original_filename=original_filename,
            content_type=file.content_type,
        )
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (InvalidFileTypeValidationError, FileSizeExceededValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except DuplicateFileError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return RawFileResponse.model_validate(raw_file)


@router.get(
    "/characterizations/{characterization_id}/files",
    response_model=list[RawFileResponse],
    summary="List raw files for a characterization run",
)
async def list_characterization_files(
    characterization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RawFileResponse]:
    """Return all raw files uploaded for an authorized characterization run."""
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        ch = await service.get_by_id(characterization_id, project_id=target_project_id)
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [RawFileResponse.model_validate(f) for f in ch.raw_files]
