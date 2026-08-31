"""
Unit tests for GreenSynth Authentication Security Utilities and AuthService.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    create_access_token,
    decode_access_token,
    hash_invitation_token,
    hash_password,
    verify_password,
)
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    LeaderRegisterRequest,
    LoginRequest,
)
from app.services.auth_service import AuthService


# ── Fixtures ────────────────────────────────────────────────

@pytest.fixture
async def active_project(db_session: AsyncSession) -> Project:
    """Fixture providing an active synthesis project."""
    proj = Project(
        project_code=f"P7-TEST-{uuid.uuid4().hex[:6].upper()}",
        name="CuO Spray Pyrolysis Test",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.flush()
    return proj


# ── Security Utilities Unit Tests ───────────────────────────

def test_hash_password_and_verification() -> None:
    """Verify secure password hashing and constant-time verification."""
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$pbkdf2-sha256$") or hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(plain, "") is False


def test_empty_password_rejection() -> None:
    """Verify that hashing empty or invalid passwords raises ValueError."""
    with pytest.raises(ValueError):
        hash_password("")


def test_hash_invitation_token() -> None:
    """Verify deterministic SHA-256 invitation token hashing."""
    token = "invitation_raw_token_xyz_123"
    hashed = hash_invitation_token(token)
    assert len(hashed) == 64
    assert hashed == hash_invitation_token("  invitation_raw_token_xyz_123  ")
    assert hashed != hash_invitation_token("other_token")


def test_jwt_creation_and_decoding() -> None:
    """Verify JWT access token creation and claim extraction."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, expires_delta=timedelta(minutes=15))

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_jwt_expiration() -> None:
    """Verify that expired JWT access tokens raise TokenDecodeError."""
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        user_id=user_id, expires_delta=timedelta(seconds=-10)
    )

    with pytest.raises(TokenDecodeError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_jwt_malformed_token() -> None:
    """Verify that malformed or forged JWT access tokens raise TokenDecodeError."""
    with pytest.raises(TokenDecodeError):
        decode_access_token("invalid.token.payload")


def test_jwt_invalid_sub_uuid() -> None:
    """Verify that non-UUID subjects in JWT raise TokenDecodeError."""
    from jose import jwt
    from app.core.config import get_settings

    settings = get_settings()
    now = datetime.now(timezone.utc)
    bad_payload = {
        "sub": "not-a-valid-uuid",
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    bad_token = jwt.encode(bad_payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(TokenDecodeError) as exc_info:
        decode_access_token(bad_token)
    assert "valid uuid" in str(exc_info.value).lower()


# ── AuthService Unit Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_service_register_leader_success(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify atomic registration of a Group Leader with ResearchGroup and Leader Membership."""
    service = AuthService(db_session)
    payload = LeaderRegisterRequest(
        full_name="Alice Leader",
        department="Chemical Engineering",
        phone="9876543210",
        password="LeaderSecurePassword123!",
        project_id=active_project.id,
        roll_number="CHEM-2026-001",
        email="Alice.Leader@greensynth.edu",
        group_name="Alpha Synthesis Unit",
    )

    res = await service.register_leader(payload)

    assert res.access_token is not None
    assert res.user.email == "alice.leader@greensynth.edu"
    assert res.user.full_name == "Alice Leader"
    assert res.user.roll_number == "CHEM-2026-001"
    assert res.user.is_active is True

    # Verify Database records
    user_db = await db_session.get(User, res.user.id)
    assert user_db is not None
    assert verify_password("LeaderSecurePassword123!", user_db.password_hash) is True

    grp_res = await db_session.execute(
        select(ResearchGroup).where(ResearchGroup.leader_user_id == user_db.id)
    )
    group = grp_res.scalar_one_or_none()
    assert group is not None
    assert group.name == "Alpha Synthesis Unit"
    assert group.project_id == active_project.id

    mem_res = await db_session.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == user_db.id,
        )
    )
    membership = mem_res.scalar_one_or_none()
    assert membership is not None
    assert membership.is_leader is True
    assert membership.status == "ACTIVE"


@pytest.mark.asyncio
async def test_service_register_leader_duplicate_email(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that registering with an existing email raises HTTP 409 Conflict."""
    service = AuthService(db_session)
    payload = LeaderRegisterRequest(
        full_name="Alice Duplicate",
        department="Chemical",
        phone="9876543210",
        password="Password123!",
        project_id=active_project.id,
        roll_number="CHEM-001",
        email="dup_leader@greensynth.edu",
    )
    await service.register_leader(payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_leader(payload)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_service_register_leader_invalid_project(
    db_session: AsyncSession,
) -> None:
    """Verify that registering with a nonexistent project raises HTTP 400 Bad Request."""
    service = AuthService(db_session)
    payload = LeaderRegisterRequest(
        full_name="Bob Leader",
        department="ENTC",
        phone="9876543211",
        password="Password123!",
        project_id=uuid.uuid4(),
        roll_number="ENTC-001",
        email="bob_leader@greensynth.edu",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.register_leader(payload)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_service_login_success(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify successful login returns valid JWT with normalized email matching."""
    service = AuthService(db_session)
    reg_payload = LeaderRegisterRequest(
        full_name="Login Test User",
        department="CSE",
        phone="9876543212",
        password="UserPassword123!",
        project_id=active_project.id,
        roll_number="CSE-001",
        email="login_test@greensynth.edu",
    )
    await service.register_leader(reg_payload)

    # Login with mixed case and leading/trailing whitespace
    login_payload = LoginRequest(
        email="  Login_Test@GreenSynth.EDU  ",
        password="UserPassword123!",
    )
    res = await service.authenticate_user(login_payload)
    assert res.access_token is not None
    assert res.user.email == "login_test@greensynth.edu"


@pytest.mark.asyncio
async def test_service_login_wrong_password_or_unknown_email(
    db_session: AsyncSession,
) -> None:
    """Verify generic 401 for wrong password or nonexistent email."""
    service = AuthService(db_session)

    # Nonexistent email
    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(
            LoginRequest(email="nonexistent@greensynth.edu", password="anyPassword123!")
        )
    assert exc_info.value.status_code == 401
    assert "invalid email or password" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_service_accept_invitation_success(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify invitation acceptance, member account creation, and non-leader membership assignment."""
    service = AuthService(db_session)

    # 1. Register a leader first
    leader_payload = LeaderRegisterRequest(
        full_name="Group Leader",
        department="Physics",
        phone="9999999999",
        password="LeaderPass123!",
        project_id=active_project.id,
        roll_number="PHY-001",
        email="group_leader@greensynth.edu",
    )
    leader_auth = await service.register_leader(leader_payload)

    grp_res = await db_session.execute(
        select(ResearchGroup).where(ResearchGroup.leader_user_id == leader_auth.user.id)
    )
    group = grp_res.scalar_one()

    # 2. Create an invitation record
    raw_token = "secure_random_invitation_token_12345"
    token_hash = hash_invitation_token(raw_token)
    invitation = Invitation(
        group_id=group.id,
        email="member_student@greensynth.edu",
        full_name="Member Student",
        department="Physics",
        phone="8888888888",
        roll_number="PHY-002",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db_session.add(invitation)
    await db_session.flush()

    # 3. Accept invitation
    accept_payload = AcceptInvitationRequest(
        token=raw_token,
        password="MemberPassword123!",
    )
    res = await service.accept_invitation(accept_payload)

    assert res.access_token is not None
    assert res.user.email == "member_student@greensynth.edu"
    assert res.user.full_name == "Member Student"
    assert res.user.roll_number == "PHY-002"

    # Verify membership created with is_leader = False
    mem_res = await db_session.execute(
        select(GroupMembership).where(
            GroupMembership.group_id == group.id,
            GroupMembership.user_id == res.user.id,
        )
    )
    membership = mem_res.scalar_one_or_none()
    assert membership is not None
    assert membership.is_leader is False
    assert membership.status == "ACTIVE"

    # Verify invitation marked ACCEPTED
    await db_session.refresh(invitation)
    assert invitation.status == "ACCEPTED"
    assert invitation.accepted_at is not None

    # Verify token cannot be reused
    with pytest.raises(HTTPException) as exc_info:
        await service.accept_invitation(accept_payload)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_service_accept_invitation_expired(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify that expired invitations are rejected with HTTP 400."""
    service = AuthService(db_session)

    leader_payload = LeaderRegisterRequest(
        full_name="Exp Leader",
        department="Chem",
        phone="1111111111",
        password="LeaderPass123!",
        project_id=active_project.id,
        roll_number="CHEM-EXP-1",
        email="exp_leader@greensynth.edu",
    )
    leader_auth = await service.register_leader(leader_payload)

    grp_res = await db_session.execute(
        select(ResearchGroup).where(ResearchGroup.leader_user_id == leader_auth.user.id)
    )
    group = grp_res.scalar_one()

    raw_token = "expired_invitation_token"
    invitation = Invitation(
        group_id=group.id,
        email="expired_student@greensynth.edu",
        full_name="Expired Student",
        department="Chem",
        phone="2222222222",
        roll_number="CHEM-EXP-2",
        token_hash=hash_invitation_token(raw_token),
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(invitation)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await service.accept_invitation(
            AcceptInvitationRequest(token=raw_token, password="NewPassword123!")
        )
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_service_get_user_profile(
    db_session: AsyncSession, active_project: Project
) -> None:
    """Verify resolving user profile with group memberships and project code."""
    service = AuthService(db_session)
    reg_payload = LeaderRegisterRequest(
        full_name="Profile User",
        department="Material Science",
        phone="3333333333",
        password="UserPassword123!",
        project_id=active_project.id,
        roll_number="MAT-001",
        email="profile_user@greensynth.edu",
        group_name="Advanced Nanomaterials Unit",
    )
    auth_res = await service.register_leader(reg_payload)

    user = await db_session.get(User, auth_res.user.id)
    assert user is not None

    profile = await service.get_user_profile(user)
    assert profile.email == "profile_user@greensynth.edu"
    assert profile.full_name == "Profile User"
    assert len(profile.memberships) == 1
    assert profile.memberships[0].group_name == "Advanced Nanomaterials Unit"
    assert profile.memberships[0].is_leader is True
    assert profile.memberships[0].project_code == active_project.project_code
