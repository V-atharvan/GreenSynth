"""
GreenSynth Analytics — Authentication Endpoints

Exposes endpoints for Group Leader registration, user login, invitation onboarding,
and authenticated user profile retrieval.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    ChangePasswordRequest,
    LeaderRegisterRequest,
    LoginRequest,
    ProfileUpdateRequest,
    TokenResponse,
    UserProfile,
    UserRead,
)
from app.schemas.common import APIResponse
from app.schemas.group import (
    AcceptInvitationPayload,
    InvitationSummary,
    InvitationValidationResponse,
)
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register-leader",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Group Leader and initialize Research Group",
    description=(
        "Registers a new student Group Leader, creates their Research Group associated "
        "with the selected Project, creates their leader membership, and returns a JWT access token."
    ),
)
async def register_leader(
    payload: LeaderRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Register a new research group leader."""
    auth_service = AuthService(db)
    token_response = await auth_service.register_leader(payload)
    return APIResponse(
        data=token_response,
        message="Group Leader registered successfully.",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates an existing user via email and password, returning a signed JWT access token.",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Authenticate user and issue JWT."""
    auth_service = AuthService(db)
    token_response = await auth_service.authenticate_user(payload)
    return APIResponse(
        data=token_response,
        message="Authentication successful.",
    )


@router.post(
    "/accept-invitation",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Accept Member Invitation",
    description=(
        "Validates an onboarding invitation token, sets the member password, "
        "activates the account, joins the research group, and returns a JWT access token."
    ),
)
async def accept_invitation(
    payload: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Accept invitation and activate member account."""
    auth_service = AuthService(db)
    token_response = await auth_service.accept_invitation(payload)
    return APIResponse(
        data=token_response,
        message="Invitation accepted and account activated successfully.",
    )


@router.get(
    "/invitations/validate",
    response_model=APIResponse[InvitationValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate Member Onboarding Token",
    description="Pre-validates an onboarding token and returns safe group & project information.",
)
async def validate_invitation(
    token: str = Query(..., min_length=1, description="Raw onboarding token"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationValidationResponse]:
    """Validate an invitation token before member account creation."""
    inv_service = InvitationService(db)
    validation_info = await inv_service.validate_invitation(token)
    return APIResponse(
        data=validation_info,
        message="Invitation token is valid.",
    )


@router.post(
    "/invitations/accept",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Accept Member Invitation and Set Password",
    description="Validates onboarding token, creates student account, joins group, and returns JWT.",
)
async def accept_invitation_v2(
    payload: AcceptInvitationPayload,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Accept member invitation and onboard student."""
    inv_service = InvitationService(db)
    token_response = await inv_service.accept_invitation(payload)
    return APIResponse(
        data=token_response,
        message="Invitation accepted and account activated successfully.",
    )


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_200_OK,
    summary="Resend Member Invitation",
    description="Regenerates an invitation token and re-dispatches the onboarding email. Leader only.",
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Resend a pending invitation to a group member."""
    inv_service = InvitationService(db)
    summary = await inv_service.resend_invitation(invitation_id, current_user)
    return APIResponse(
        data=summary,
        message="Invitation resent successfully.",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserProfile],
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
    description=(
        "Returns profile information and group memberships for the current user. "
        "Requires Bearer token authentication."
    ),
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfile]:
    """Retrieve current authenticated user details."""
    auth_service = AuthService(db)
    profile = await auth_service.get_user_profile(current_user)
    return APIResponse(
        data=profile,
        message="User profile retrieved successfully.",
    )


@router.patch(
    "/me",
    response_model=APIResponse[UserProfile],
    status_code=status.HTTP_200_OK,
    summary="Update Current Authenticated User Profile",
    description="Updates permitted profile fields (full name, department, phone, roll number).",
)
async def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfile]:
    """Update current user profile attributes."""
    auth_service = AuthService(db)
    updated_profile = await auth_service.update_user_profile(current_user, payload)
    return APIResponse(
        data=updated_profile,
        message="Profile updated successfully.",
    )


@router.post(
    "/change-password",
    response_model=APIResponse[dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="Change User Password",
    description="Verifies current password and updates to a new cryptographically hashed password.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict[str, str]]:
    """Change authenticated user password."""
    auth_service = AuthService(db)
    result = await auth_service.change_password(current_user, payload)
    return APIResponse(
        data=result,
        message="Password changed successfully.",
    )



@router.get(
    "/users",
    response_model=APIResponse[list[UserRead]],
    status_code=status.HTTP_200_OK,
    summary="List All System Users (Admin Only)",
    description="Returns all registered users in the system. Restricted to System Administrators.",
)
async def list_users(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[UserRead]]:
    """Retrieve all users (Admin only)."""
    auth_service = AuthService(db)
    users = await auth_service.list_all_users()
    return APIResponse(
        data=users,
        message="All system users retrieved successfully.",
    )


@router.post(
    "/logout",
    response_model=APIResponse[dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Stateless token logout endpoint. Informs client to clear local credentials.",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict[str, str]]:
    """Stateless logout endpoint."""
    return APIResponse(
        data={"status": "logged_out"},
        message="Logout successful. Please clear local authorization tokens.",
    )
