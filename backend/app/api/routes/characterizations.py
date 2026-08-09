"""
GreenSynth Analytics — Characterizations API Router

REST API endpoints for laboratory characterizations and raw file uploads.
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

from app.api.deps import get_db
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
from app.services.sample_service import SampleNotFoundError

router = APIRouter(tags=["characterizations"])


@router.post(
    "/characterizations",
    response_model=CharacterizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create characterization run metadata",
)
async def create_characterization(
    data: CharacterizationCreate,
    db: AsyncSession = Depends(get_db),
) -> CharacterizationResponse:
    """Create a new laboratory characterization run for a sample."""
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
    db: AsyncSession = Depends(get_db),
) -> CharacterizationResponse:
    """Get single characterization record with associated raw files."""
    service = CharacterizationService(db)
    try:
        ch = await service.get_by_id(characterization_id)
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
    db: AsyncSession = Depends(get_db),
) -> list[CharacterizationResponse]:
    """Return all characterization runs linked to a physical sample."""
    service = CharacterizationService(db)
    chs = await service.list_sample_characterizations(sample_id)
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
    db: AsyncSession = Depends(get_db),
) -> RawFileResponse:
    """
    Upload an immutable raw laboratory data file for a characterization run.

    Calculates SHA-256 checksum, verifies format compatibility with the technique,
    and detects duplicate uploads.
    """
    service = CharacterizationService(db)
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
    db: AsyncSession = Depends(get_db),
) -> list[RawFileResponse]:
    """Return all raw files uploaded for a characterization run."""
    service = CharacterizationService(db)
    try:
        ch = await service.get_by_id(characterization_id)
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [RawFileResponse.model_validate(f) for f in ch.raw_files]
