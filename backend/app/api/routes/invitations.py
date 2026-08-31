"""
GreenSynth Analytics — Public & Admin Invitation Endpoints

Exposes:
1. Public token validation endpoint (/api/v1/invitations/validate/{token})
2. System-wide invitation listings for Administrators (/api/v1/invitations)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.common import APIResponse
from app.schemas.group import (
    AcceptInvitationPayload,
    InvitationSummary,
    InvitationValidationResponse,
)
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.get(
    "/validate/{token}",
    response_model=APIResponse[InvitationValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate Member Invitation Token (Path Param)",
    description="Public endpoint to validate an onboarding token and retrieve safe group/project metadata.",
)
async def validate_invitation_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationValidationResponse]:
    """Validate token and return sanitized group & project metadata."""
    service = InvitationService(db)
    validation = await service.validate_invitation(token)
    return APIResponse(
        data=validation,
        message="Invitation token is valid.",
    )


@router.get(
    "/validate",
    response_model=APIResponse[InvitationValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate Member Invitation Token (Query Param)",
    description="Public endpoint to validate an onboarding token via query parameter.",
)
async def validate_invitation_query(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationValidationResponse]:
    """Validate token passed via query parameter and return sanitized group & project metadata."""
    service = InvitationService(db)
    validation = await service.validate_invitation(token)
    return APIResponse(
        data=validation,
        message="Invitation token is valid.",
    )


@router.post(
    "/accept",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Accept Member Invitation & Activate Account",
    description="Public endpoint to accept an invitation, create/activate student account, join research group, and return session.",
)
async def accept_invitation(
    payload: AcceptInvitationPayload,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Accept member invitation and set student account password."""
    service = InvitationService(db)
    token_response = await service.accept_invitation(payload)
    return APIResponse(
        data=token_response,
        message="Invitation accepted and account activated successfully.",
    )


@router.get(
    "/",
    response_model=APIResponse[list[InvitationSummary]],
    status_code=status.HTTP_200_OK,
    summary="List All Invitations System-Wide (Admin)",
    description="Returns all invitation records across all research groups. Restricted to System Administrators.",
)
async def list_all_invitations(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[InvitationSummary]]:
    """List all invitations system-wide."""
    service = InvitationService(db)
    invitations = await service.list_all_invitations(admin_user)
    return APIResponse(
        data=invitations,
        message="All invitations retrieved successfully.",
    )
