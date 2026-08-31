"""
GreenSynth Analytics — Unit Tests: InvitationService

Verifies:
  - Token validation and pre-check data sanitization
  - Member onboarding and account activation
  - One-time-use token consumption and expiration
  - Leader-controlled invitation re-issuance
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_secure_invitation_token, hash_invitation_token
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.group import (
    AcceptInvitationPayload,
    GroupMetadataInput,
    GroupRegistrationRequest,
    LeaderRegisterInput,
    MemberInvitationInput,
)
from app.services.group_service import GroupService
from app.services.invitation_service import InvitationService


@pytest.fixture
async def setup_group(
    db_session: AsyncSession,
) -> tuple[User, ResearchGroup, Project, str, Invitation]:
    """Helper fixture establishing an active research group with one pending invitation."""
    # 1. Project
    project = Project(
        project_code=f"P7-INV-{uuid.uuid4().hex[:6].upper()}",
        name="Invitation Test Project",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(project)
    await db_session.flush()

    # 2. Leader
    leader = User(
        username="inv_leader_test",
        email="leader.inv@greensynth.edu",
        full_name="Leader Inv",
        department="Physics",
        phone="1234567890",
        roll_number="PHY-L1",
        role="RESEARCHER",
        password_hash="hash",
        is_active=True,
    )
    db_session.add(leader)
    await db_session.flush()

    # 3. Group
    group = ResearchGroup(
        name="Physics Nanotech Group",
        project_id=project.id,
        leader_user_id=leader.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group)
    await db_session.flush()

    # 4. Leader Membership
    membership = GroupMembership(
        group_id=group.id,
        user_id=leader.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership)
    await db_session.flush()

    # 5. Invitation with raw token
    raw_token = generate_secure_invitation_token()
    invitation = Invitation(
        group_id=group.id,
        email="invited.student@greensynth.edu",
        full_name="Invited Student",
        department="Physics",
        phone="9999999999",
        roll_number="PHY-M1",
        token_hash=hash_invitation_token(raw_token),
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db_session.add(invitation)
    await db_session.flush()

    return leader, group, project, raw_token, invitation


@pytest.mark.asyncio
async def test_validate_invitation_success(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify validation returns safe group, project, and invited student metadata."""
    leader, group, project, raw_token, invitation = setup_group
    service = InvitationService(db_session)

    res = await service.validate_invitation(raw_token)
    assert res.valid is True
    assert res.group_name == "Physics Nanotech Group"
    assert res.project_code == project.project_code
    assert res.project_name == project.name
    assert res.invited_name == "Invited Student"
    assert res.invited_email == "invited.student@greensynth.edu"
    assert res.department == "Physics"
    assert res.roll_number == "PHY-M1"
    assert res.leader_name == "Leader Inv"


@pytest.mark.asyncio
async def test_validate_invitation_invalid_token(
    db_session: AsyncSession,
) -> None:
    """Verify validating a non-existent token raises 400 Bad Request."""
    service = InvitationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.validate_invitation("bogus_token_12345")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_invitation_expired(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify validating an expired token raises 400 Bad Request."""
    leader, group, project, raw_token, invitation = setup_group
    invitation.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.flush()

    service = InvitationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.validate_invitation(raw_token)
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_accept_invitation_success(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify accepting invitation onboards student and issues JWT."""
    leader, group, project, raw_token, invitation = setup_group
    service = InvitationService(db_session)

    payload = AcceptInvitationPayload(
        token=raw_token,
        password="MemberSecurePassword123!",
        confirm_password="MemberSecurePassword123!",
    )
    auth_res = await service.accept_invitation(payload)

    # 1. Verify Auth Response
    assert auth_res.access_token is not None
    assert auth_res.user.email == "invited.student@greensynth.edu"
    assert auth_res.user.full_name == "Invited Student"
    assert auth_res.user.roll_number == "PHY-M1"

    # 2. Verify Membership in DB
    mem_res = await db_session.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == auth_res.user.id,
        )
    )
    membership = mem_res.scalar_one_or_none()
    assert membership is not None
    assert membership.is_leader is False
    assert membership.status == "ACTIVE"

    # 3. Verify Invitation Status
    await db_session.refresh(invitation)
    assert invitation.status == "ACCEPTED"
    assert invitation.accepted_at is not None

    # 4. Verify Token Cannot be Reused
    with pytest.raises(HTTPException) as exc_info:
        await service.accept_invitation(payload)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_accept_invitation_password_mismatch(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify password mismatch raises 422 Unprocessable Entity."""
    leader, group, project, raw_token, invitation = setup_group
    service = InvitationService(db_session)

    payload = AcceptInvitationPayload(
        token=raw_token,
        password="Password123!",
        confirm_password="DifferentPassword123!",
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.accept_invitation(payload)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_resend_invitation_by_leader(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify leader can resend invitation, regenerating token hash and extending expiry."""
    leader, group, project, raw_token, invitation = setup_group
    service = InvitationService(db_session)

    old_hash = invitation.token_hash
    res = await service.resend_invitation(invitation.id, leader)

    assert res.id == invitation.id
    assert res.status == "PENDING"

    await db_session.refresh(invitation)
    assert invitation.token_hash != old_hash  # New token hash generated


@pytest.mark.asyncio
async def test_resend_invitation_non_leader_forbidden(
    db_session: AsyncSession, setup_group: tuple
) -> None:
    """Verify non-leader attempting to resend invitation raises 403 Forbidden."""
    leader, group, project, raw_token, invitation = setup_group
    service = InvitationService(db_session)

    other_user = User(
        username="unauthorized_student",
        email="other@greensynth.edu",
        full_name="Other Student",
        department="Physics",
        phone="0000000000",
        roll_number="PHY-OTHER",
        role="RESEARCHER",
        password_hash="hash",
    )
    db_session.add(other_user)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await service.resend_invitation(invitation.id, other_user)
    assert exc_info.value.status_code == 403
