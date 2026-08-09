"""
GreenSynth Analytics — Files API Router

REST API endpoints for raw file metadata retrieval and file downloading.
"""

from __future__ import annotations

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.characterization import RawFileResponse
from app.services.characterization_service import (
    CharacterizationService,
    RawFileNotFoundError,
)

router = APIRouter(prefix="/files", tags=["files"])


@router.get(
    "/{file_id}",
    response_model=RawFileResponse,
    summary="Get raw file metadata",
)
async def get_file_metadata(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RawFileResponse:
    """Return metadata (checksum, size, original filename, storage status) for a raw file."""
    service = CharacterizationService(db)
    try:
        raw_file = await service.get_raw_file_by_id(file_id)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return RawFileResponse.model_validate(raw_file)


@router.get(
    "/{file_id}/download",
    summary="Download original raw laboratory file",
)
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Download the original, un-modified laboratory raw file.

    Preserves original filename and MIME type.
    """
    service = CharacterizationService(db)
    try:
        content, original_filename, mime_type = await service.download_raw_file(file_id)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    encoded_filename = quote(original_filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Content-Type": mime_type,
    }
    return Response(content=content, media_type=mime_type, headers=headers)
