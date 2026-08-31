"""
GreenSynth Analytics — Research Group Endpoints

Exposes endpoints for multi-member group registration, group listings,
group details, member rosters, and invitation management.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.group import (
    CreateInvitationRequest,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupRegistrationRequest,
    GroupRegistrationResponse,
    InvitationSummary,
    MemberInvitationInput,
)
from app.services.group_service import GroupService
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/groups", tags=["Research Groups"])


@router.post(
    "/register",
    response_model=APIResponse[GroupRegistrationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Research Group with Leader and Member Invitations",
    description=(
        "Atomically registers a Group Leader, initializes their Research Group bound to "
        "the selected Project, creates the Leader membership, and generates onboarding "
        "invitations with emails for the remaining group members."
    ),
)
async def register_group(
    payload: GroupRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GroupRegistrationResponse]:
    """Register a new research group and invite members."""
    service = GroupService(db)
    response = await service.register_group_with_members(payload)
    return APIResponse(
        data=response,
        message="Research group registered and member invitations created successfully.",
    )


@router.get(
    "/",
    response_model=APIResponse[list[GroupDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="List All Research Groups (Admin Only)",
    description="Returns all active research groups across all synthesis projects. Restricted to System Administrators.",
)
async def list_all_groups(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[GroupDetailResponse]]:
    """List all research groups across all projects (Admin)."""
    service = GroupService(db)
    groups = await service.list_all_groups()
    return APIResponse(
        data=groups,
        message="All research groups retrieved successfully.",
    )


@router.get(
    "/me",
    response_model=APIResponse[GroupDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User's Research Group",
    description="Returns metadata, project binding, and capacity for the authenticated user's research group.",
)
async def get_my_group(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GroupDetailResponse]:
    """Retrieve current research group details."""
    service = GroupService(db)
    group_detail = await service.get_my_group(current_user)
    return APIResponse(
        data=group_detail,
        message="Research group details retrieved successfully.",
    )


@router.get(
    "/me/members",
    response_model=APIResponse[list[GroupMemberResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Active Group Members",
    description="Returns all active members in the current authenticated user's research group.",
)
async def get_my_group_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[GroupMemberResponse]]:
    """List members of the user's research group."""
    service = GroupService(db)
    members = await service.get_my_group_members(current_user)
    return APIResponse(
        data=members,
        message="Group members retrieved successfully.",
    )


@router.get(
    "/me/invitations",
    response_model=APIResponse[list[InvitationSummary]],
    status_code=status.HTTP_200_OK,
    summary="List Group Member Invitations",
    description="Returns all invitation statuses (Pending, Accepted, Expired) for the user's research group.",
)
async def get_my_group_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[InvitationSummary]]:
    """List invitation records for the research group."""
    service = GroupService(db)
    invitations = await service.get_my_group_invitations(current_user)
    return APIResponse(
        data=invitations,
        message="Group invitations retrieved successfully.",
    )


@router.post(
    "/me/invitations",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Invite Additional Member",
    description="Allows the Group Leader to invite an additional member if group is under maximum capacity.",
)
async def invite_member(
    payload: MemberInvitationInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Invite an additional student to the research group."""
    service = GroupService(db)
    invitation = await service.invite_member_to_my_group(current_user, payload)
    return APIResponse(
        data=invitation,
        message="Member invitation sent successfully.",
    )


@router.get(
    "/{group_id}",
    response_model=APIResponse[GroupDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Research Group Details by ID",
)
async def get_group_by_id(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[GroupDetailResponse]:
    """Get research group by ID (Admin or group member)."""
    service = GroupService(db)
    if not current_user.is_admin:
        # Verify user belongs to this group
        my_group = await service.get_my_group(current_user)
        if my_group.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this research group.")
    group_detail = await service.get_group_by_id(group_id)
    return APIResponse(data=group_detail, message="Group details retrieved successfully.")


@router.get(
    "/{group_id}/members",
    response_model=APIResponse[list[GroupMemberResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get Research Group Members by ID",
)
async def get_group_members_by_id(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[GroupMemberResponse]]:
    """Get research group members by ID (Admin or group member)."""
    service = GroupService(db)
    if not current_user.is_admin:
        my_group = await service.get_my_group(current_user)
        if my_group.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this research group.")
    members = await service.get_group_members_by_id(group_id)
    return APIResponse(data=members, message="Group members retrieved successfully.")


@router.post(
    "/{group_id}/invitations",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Invite Member to Research Group",
    description="Creates a new onboarding invitation for the research group. Restricted to Group Leader or Admin.",
)
async def create_group_invitation(
    group_id: uuid.UUID,
    payload: CreateInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Create a new member invitation for the specified research group."""
    inv_service = InvitationService(db)
    invitation = await inv_service.create_invitation(group_id, payload, current_user)
    return APIResponse(
        data=invitation,
        message="Member invitation created and email dispatched successfully.",
    )


@router.get(
    "/{group_id}/invitations",
    response_model=APIResponse[list[InvitationSummary]],
    status_code=status.HTTP_200_OK,
    summary="List Research Group Invitations",
    description="Returns all invitation records for the specified research group. Restricted to Group Leader or Admin.",
)
async def list_group_invitations_by_id(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[InvitationSummary]]:
    """List all invitations for the specified research group."""
    inv_service = InvitationService(db)
    invitations = await inv_service.list_group_invitations(group_id, current_user)
    return APIResponse(
        data=invitations,
        message="Group invitations retrieved successfully.",
    )


@router.post(
    "/{group_id}/invitations/{invitation_id}/resend",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_200_OK,
    summary="Resend Research Group Invitation",
    description="Regenerates token and resends onboarding email. Restricted to Group Leader or Admin with 60s cooldown.",
)
async def resend_group_invitation(
    group_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Resend an onboarding invitation."""
    inv_service = InvitationService(db)
    invitation = await inv_service.resend_invitation(invitation_id, current_user, group_id)
    return APIResponse(
        data=invitation,
        message="Invitation token regenerated and email dispatched successfully.",
    )


@router.delete(
    "/{group_id}/invitations/{invitation_id}",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_200_OK,
    summary="Revoke Research Group Invitation",
    description="Revokes a pending invitation and invalidates the token. Restricted to Group Leader or Admin.",
)
async def revoke_group_invitation(
    group_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Revoke an onboarding invitation."""
    inv_service = InvitationService(db)
    invitation = await inv_service.revoke_invitation(invitation_id, current_user, group_id)
    return APIResponse(
        data=invitation,
        message="Invitation revoked successfully.",
    )


@router.post(
    "/{group_id}/invitations/{invitation_id}/revoke",
    response_model=APIResponse[InvitationSummary],
    status_code=status.HTTP_200_OK,
    summary="Revoke Research Group Invitation (POST alias)",
    description="Revokes a pending invitation and invalidates the token. Restricted to Group Leader or Admin.",
)
async def revoke_group_invitation_post_alias(
    group_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InvitationSummary]:
    """Revoke an onboarding invitation (POST alias)."""
    inv_service = InvitationService(db)
    invitation = await inv_service.revoke_invitation(invitation_id, current_user, group_id)
    return APIResponse(
        data=invitation,
        message="Invitation revoked successfully.",
    )
