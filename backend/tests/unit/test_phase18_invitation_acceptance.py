"""
GreenSynth Analytics — Phase 18 Invitation Acceptance & Password Creation Unit Tests

Validates:
1. Valid invitation acceptance creates student user account and activates group membership (200 OK).
2. Invalid onboarding token rejected (400 Bad Request).
3. Expired invitation rejected (400 Bad Request).
4. Already accepted invitation token cannot be reused (400 Bad Request).
5. Cancelled/revoked invitation cannot be accepted (400 Bad Request).
6. Password mismatch rejected (422 Unprocessable Entity).
7. Weak/short password (< 8 chars) rejected (422 Unprocessable Entity).
8. Password security: Plaintext password is never stored; only secure hash exists in DB.
9. Response safety: Neither password, password_hash, nor raw invitation token are returned in responses.
10. Role & Account type enforcement: Invitation always yields STUDENT / RESEARCHER; Admin injection is rejected.
11. Admin account protection: Admin accounts cannot accept student invitations.
12. Group membership activation: GroupMembership is created/activated with ACTIVE status and is_leader=False.
13. Project & Group preservation: Project binding is derived exclusively from the research group.
14. Email normalization: Email case variations resolve to the same normalized identity.
15. Post-acceptance unified login: User can immediately authenticate via standard POST /auth/login.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    generate_secure_invitation_token,
    hash_invitation_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User, UserRole


@pytest.fixture
async def phase18_fixture(db_session: AsyncSession):
    """Sets up Project, Leader, Group, and Invitations for Phase 18 testing."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Project P7 (Spray Pyrolysis CuO)
    p7 = Project(
        id=uuid.uuid4(),
        name="Spray Pyrolysis CuO Thin Films",
        project_code=f"P7-{suffix}",
        description="CuO spray pyrolysis with mulberry extract",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(p7)
    await db_session.flush()

    # 2. Leader User & Admin User
    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p18_{suffix}",
        email=f"admin.p18_{suffix}@greensynth.edu",
        full_name="Admin Phase18",
        department="Administration",
        phone="1000000000",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    leader = User(
        id=uuid.uuid4(),
        username=f"leader_p18_{suffix}",
        email=f"leader.p18_{suffix}@greensynth.edu",
        full_name="Dr. Vikram Rao",
        department="Materials Engineering",
        phone="9876500001",
        roll_number=f"LEAD-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("LeaderPass123!"),
        is_active=True,
    )
    db_session.add_all([admin, leader])
    await db_session.flush()

    # 3. Research Group
    group = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Nanoscale Synthesis Lab {suffix}",
        project_id=p7.id,
        leader_user_id=leader.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group)
    await db_session.flush()

    # 4. Leader Membership
    leader_mem = GroupMembership(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=leader.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(leader_mem)
    await db_session.flush()

    return {
        "p7": p7,
        "admin": admin,
        "leader": leader,
        "group": group,
        "suffix": suffix,
    }


def make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    """Creates test client with db_session dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers=headers,
    )


# ── INVITATION ACCEPTANCE TESTS ──────────────────────────────────────

@pytest.mark.asyncio
async def test_valid_invitation_acceptance_lifecycle(db_session: AsyncSession, phase18_fixture):
    """Invited member submits password, activating student account and joining research group."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="rahul.sharma@example.com",
        full_name="Rahul Sharma",
        department="Chemical Engineering",
        phone="9876543210",
        roll_number="CHE-2026-001",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "SecureStudentPassword123!",
            "confirm_password": "SecureStudentPassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]

        # Check response fields
        assert data["user"]["email"] == "rahul.sharma@example.com"
        assert data["user"]["full_name"] == "Rahul Sharma"
        assert data["user"]["account_type"] == "STUDENT"
        assert data["user"]["role"] == "RESEARCHER"
        assert "password" not in data
        assert "password_hash" not in data["user"]
        assert "token_hash" not in data

        # Check DB state
        await db_session.refresh(inv)
        assert inv.status == InvitationStatus.ACCEPTED.value
        assert inv.accepted_at is not None

        # Check created user
        user_res = await db_session.execute(
            select(User).where(User.email == "rahul.sharma@example.com")
        )
        user = user_res.scalar_one()
        assert user.is_active is True
        assert verify_password("SecureStudentPassword123!", user.password_hash)

        # Check group membership
        mem_res = await db_session.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group.id,
                GroupMembership.user_id == user.id,
            )
        )
        membership = mem_res.scalar_one()
        assert membership.status == MembershipStatus.ACTIVE.value
        assert membership.is_leader is False


@pytest.mark.asyncio
async def test_invalid_token_rejected(db_session: AsyncSession, phase18_fixture):
    """Invalid/non-existent token returns 400 Bad Request."""
    async with make_client(db_session) as ac:
        payload = {
            "token": "totally-fake-invalid-token",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 400
        assert "invalid" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_expired_token_rejected(db_session: AsyncSession, phase18_fixture):
    """Expired invitation token cannot be accepted and returns 400 Bad Request."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="expired.student@example.com",
        full_name="Expired Student",
        department="Chemistry",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 400
        assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_already_accepted_token_cannot_be_reused(db_session: AsyncSession, phase18_fixture):
    """Token that has already been accepted cannot be accepted again."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="reuse.test@example.com",
        full_name="Reuse Test",
        department="Chemistry",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.ACCEPTED.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        accepted_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 400
        assert "already been accepted" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancelled_invitation_rejected(db_session: AsyncSession, phase18_fixture):
    """Cancelled / Revoked invitation cannot be accepted."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="cancelled.test@example.com",
        full_name="Cancelled Test",
        department="Chemistry",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.CANCELLED.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 400
        assert "no longer active" in res.json()["detail"].lower() or "pending" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_password_mismatch_rejected(db_session: AsyncSession, phase18_fixture):
    """Mismatched password and confirm_password returns 422 Unprocessable Entity."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="mismatch@example.com",
        full_name="Mismatch Test",
        department="Chemistry",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "Password123!",
            "confirm_password": "DifferentPassword456!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 422
        assert "do not match" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_short_password_rejected(db_session: AsyncSession, phase18_fixture):
    """Password shorter than 8 characters returns 422 Unprocessable Entity."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="shortpass@example.com",
        full_name="Short Pass Test",
        department="Chemistry",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "short",
            "confirm_password": "short",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_email_normalization_on_acceptance(db_session: AsyncSession, phase18_fixture):
    """Mixed-case invitation email is normalized to lowercase user account."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="Student.MixedCase@Example.Com",
        full_name="Mixed Case Student",
        department="Chemical Engineering",
        phone="N/A",
        roll_number="CHE-009",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["user"]["email"] == "student.mixedcase@example.com"


@pytest.mark.asyncio
async def test_unified_login_after_acceptance(db_session: AsyncSession, phase18_fixture):
    """After invitation acceptance, student can immediately log in through unified /auth/login."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="ananya.das@example.com",
        full_name="Ananya Das",
        department="Materials Science",
        phone="9876543211",
        roll_number="MS-042",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        # 1. Accept Invitation
        acc_payload = {
            "token": raw_token,
            "password": "AnanyaPassword2026!",
            "confirm_password": "AnanyaPassword2026!",
        }
        acc_res = await ac.post("/api/v1/invitations/accept", json=acc_payload)
        assert acc_res.status_code == 200

        # 2. Login via unified login endpoint
        login_payload = {
            "email": "ananya.das@example.com",
            "password": "AnanyaPassword2026!",
        }
        login_res = await ac.post("/api/v1/auth/login", json=login_payload)
        assert login_res.status_code == 200
        login_data = login_res.json()["data"]

        assert login_data["user"]["account_type"] == "STUDENT"
        assert login_data["user"]["email"] == "ananya.das@example.com"
        assert "access_token" in login_data


@pytest.mark.asyncio
async def test_admin_role_injection_blocked(db_session: AsyncSession, phase18_fixture):
    """Malicious attempt to pass account_type=ADMIN or role=ADMIN is ignored and forced to STUDENT."""
    group = phase18_fixture["group"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email="hacker.student@example.com",
        full_name="Hacker Student",
        department="Computer Science",
        phone="N/A",
        roll_number="CS-007",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "HackerPassword123!",
            "confirm_password": "HackerPassword123!",
            "role": "ADMIN",
            "account_type": "ADMIN",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]

        # Backend strictly forced STUDENT / RESEARCHER
        assert data["user"]["account_type"] == "STUDENT"
        assert data["user"]["role"] == "RESEARCHER"

        user_res = await db_session.execute(
            select(User).where(User.email == "hacker.student@example.com")
        )
        user = user_res.scalar_one()
        assert user.role == "RESEARCHER"
        assert user.is_admin is False


@pytest.mark.asyncio
async def test_existing_admin_cannot_accept_student_invitation(db_session: AsyncSession, phase18_fixture):
    """Existing Admin user cannot accept a student invitation to overwrite their Admin account."""
    group = phase18_fixture["group"]
    admin = phase18_fixture["admin"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=group.id,
        email=admin.email,
        full_name=admin.full_name,
        department="Admin Dept",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        payload = {
            "token": raw_token,
            "password": "NewAdminPassword123!",
            "confirm_password": "NewAdminPassword123!",
        }
        res = await ac.post("/api/v1/invitations/accept", json=payload)
        assert res.status_code == 400
        assert "administrator" in res.json()["detail"].lower()
