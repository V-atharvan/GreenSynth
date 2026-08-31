"""
GreenSynth Analytics — Files API Router

REST API endpoints for raw file metadata retrieval and file downloading with authorization & project isolation.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_project, get_current_user, get_db
from app.models.project import Project
from app.models.user import User
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RawFileResponse:
    """Return metadata (checksum, size, original filename, storage status) for an authorized raw file."""
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        raw_file = await service.get_raw_file_by_id(file_id, project_id=target_project_id)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return RawFileResponse.model_validate(raw_file)


@router.get(
    "/{file_id}/download",
    summary="Download original raw laboratory file",
)
async def download_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Download the original, un-modified laboratory raw file for an authorized project.
    """
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        content, original_filename, mime_type = await service.download_raw_file(
            file_id, project_id=target_project_id
        )
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


@router.get(
    "/{file_id}/url",
    summary="Get temporary pre-signed direct download URL (if supported)",
)
async def get_file_download_url(
    file_id: uuid.UUID,
    expiry_seconds: int = 3600,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | None]:
    """
    Return a pre-signed direct download URL if object storage is active,
    or None if backend streaming (/files/{id}/download) should be used.
    """
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        url = await service.generate_download_url(
            file_id, project_id=target_project_id, expiry_seconds=expiry_seconds
        )
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {
        "file_id": str(file_id),
        "download_url": url,
        "direct_download_endpoint": f"/api/v1/files/{file_id}/download",
    }


@router.get(
    "/{file_id}/preview",
    summary="Preview raw laboratory file content safely",
)
async def preview_file(
    file_id: uuid.UUID,
    max_lines: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Return a safe preview (header lines and metadata) for an authorized raw file with IDOR verification.
    """
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        return await service.preview_raw_file(
            file_id, project_id=target_project_id, max_lines=max_lines
        )
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a raw laboratory file",
)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a raw laboratory data file and its storage object with IDOR verification.
    """
    service = CharacterizationService(db)
    target_project_id = None
    if not current_user.is_admin:
        current_project = await get_current_project(current_user=current_user, db=db)
        target_project_id = current_project.id

    try:
        await service.delete_raw_file(file_id, project_id=target_project_id)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

