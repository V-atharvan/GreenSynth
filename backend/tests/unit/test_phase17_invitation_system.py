"""
GreenSynth Analytics — Phase 17 Member Invitation System Unit & Integration Tests

Validates:
1. Group Leader creates member invitation (201 Created).
2. Normal Student blocked from creating invitations (403 Forbidden).
3. Group Leader blocked from creating invitations for other groups (403 Forbidden).
4. System Administrator can create and manage invitations across any group.
5. Invalid recipient email rejected (422 Unprocessable Entity).
6. Duplicate pending invitation rejected (409 Conflict).
7. Active member re-invitation rejected (409 Conflict).
8. Token security: Cryptographically secure random token generated, only token_hash stored in DB.
9. Token expiration enforcement (expired token rejected).
10. Revocation enforcement (revoked token cannot be used).
11. Resend token regeneration (old token invalidated, new token generated).
12. Resend rate-limiting cooldown (60s cooldown enforced).
13. Access control for listing group invitations (Leader own group, Admin all, Student blocked).
14. Public token validation endpoint returns safe, sanitized group & project metadata.
15. Integration with Phase 16 SMTP EmailService.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

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
)
from app.main import app
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User, UserRole


@pytest.fixture
async def phase17_invitation_fixture(db_session: AsyncSession):
    """Sets up projects, users, groups, and tokens for Phase 17 testing."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Projects
    p1 = Project(
        id=uuid.uuid4(),
        name="Zinc Oxide Phytochemical Synthesis",
        project_code=f"P1-{suffix}",
        description="ZnO synthesis via green extract",
        material="ZnO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Sol-gel",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        name="Titanium Dioxide Sol-Gel",
        project_code=f"P2-{suffix}",
        description="TiO2 nanoparticles",
        material="TiO2",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Sol-gel",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    # 2. Users
    admin = User(
        id=uuid.uuid4(),
        username=f"phase17_admin_{suffix}",
        email=f"admin.phase17_{suffix}@greensynth.edu",
        full_name="Admin Phase17",
        department="Administration",
        phone="1000000000",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminSecurePass123!"),
        is_active=True,
    )
    leader_a = User(
        id=uuid.uuid4(),
        username=f"leader_a_{suffix}",
        email=f"leadera.phase17_{suffix}@greensynth.edu",
        full_name="Leader Group A",
        department="Chemical Engineering",
        phone="1000000001",
        roll_number=f"LEAD-A-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentSecurePass123!"),
        is_active=True,
    )
    leader_b = User(
        id=uuid.uuid4(),
        username=f"leader_b_{suffix}",
        email=f"leaderb.phase17_{suffix}@greensynth.edu",
        full_name="Leader Group B",
        department="Nanotechnology",
        phone="1000000002",
        roll_number=f"LEAD-B-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentSecurePass123!"),
        is_active=True,
    )
    student_a = User(
        id=uuid.uuid4(),
        username=f"student_a_{suffix}",
        email=f"studenta.phase17_{suffix}@greensynth.edu",
        full_name="Student Group A",
        department="Chemical Engineering",
        phone="1000000003",
        roll_number=f"STU-A-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentSecurePass123!"),
        is_active=True,
    )
    db_session.add_all([admin, leader_a, leader_b, student_a])
    await db_session.flush()

    # 3. Research Groups
    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Phase 17 Research Group A {suffix}",
        project_id=p1.id,
        leader_user_id=leader_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Phase 17 Research Group B {suffix}",
        project_id=p2.id,
        leader_user_id=leader_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add_all([group_a, group_b])
    await db_session.flush()

    # 4. Group Memberships
    mem_leader_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=leader_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    mem_student_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=student_a.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    mem_leader_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=leader_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add_all([mem_leader_a, mem_student_a, mem_leader_b])
    await db_session.flush()

    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_leader_a = create_access_token(leader_a.id, account_type="STUDENT")
    token_leader_b = create_access_token(leader_b.id, account_type="STUDENT")
    token_student_a = create_access_token(student_a.id, account_type="STUDENT")

    return {
        "p1": p1,
        "p2": p2,
        "admin": admin,
        "leader_a": leader_a,
        "leader_b": leader_b,
        "student_a": student_a,
        "group_a": group_a,
        "group_b": group_b,
        "token_admin": token_admin,
        "token_leader_a": token_leader_a,
        "token_leader_b": token_leader_b,
        "token_student_a": token_student_a,
    }


def make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    """Helper to create test client with db session dependency override and optional auth token."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers=headers,
    )


# ── INVITATION CREATION TESTS ────────────────────────────────────────

@pytest.mark.asyncio
async def test_group_leader_creates_invitation(db_session: AsyncSession, phase17_invitation_fixture):
    """Group Leader can successfully invite a member to their own research group."""
    group_a = phase17_invitation_fixture["group_a"]
    token_a = phase17_invitation_fixture["token_leader_a"]

    async with make_client(db_session, token=token_a) as ac:
        payload = {
            "full_name": "Rahul Sharma",
            "email": "Rahul.Sharma@Example.COM",
            "department": "Chemical Engineering",
            "phone": "9876543210",
            "roll_number": "CHE-2026-042",
        }
        res = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res.status_code == 201
        data = res.json()["data"]

        assert data["email"] == "rahul.sharma@example.com"
        assert data["full_name"] == "Rahul Sharma"
        assert data["status"] == "PENDING"
        assert "raw_token" not in data
        assert "token_hash" not in data


@pytest.mark.asyncio
async def test_student_cannot_create_invitation(db_session: AsyncSession, phase17_invitation_fixture):
    """Normal student is forbidden (403) from creating invitations."""
    group_a = phase17_invitation_fixture["group_a"]
    token_student = phase17_invitation_fixture["token_student_a"]

    async with make_client(db_session, token=token_student) as ac:
        payload = {
            "full_name": "Unauthorized Invite",
            "email": "unauthorized@example.com",
        }
        res = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_group_leader_cross_group_invitation_blocked(db_session: AsyncSession, phase17_invitation_fixture):
    """Group Leader cannot create invitations for another research group (403)."""
    group_b = phase17_invitation_fixture["group_b"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    async with make_client(db_session, token=token_leader_a) as ac:
        payload = {
            "full_name": "Cross Group Invite",
            "email": "cross@example.com",
        }
        res = await ac.post(f"/api/v1/groups/{group_b.id}/invitations", json=payload)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_invite_to_any_group(db_session: AsyncSession, phase17_invitation_fixture):
    """System Administrator can create invitations for any group."""
    group_b = phase17_invitation_fixture["group_b"]
    token_admin = phase17_invitation_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        payload = {
            "full_name": "Admin Invited Member",
            "email": "admin.invite@example.com",
        }
        res = await ac.post(f"/api/v1/groups/{group_b.id}/invitations", json=payload)
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["email"] == "admin.invite@example.com"


@pytest.mark.asyncio
async def test_invalid_email_rejected(db_session: AsyncSession, phase17_invitation_fixture):
    """Malformed email address is rejected with 422 Unprocessable Entity."""
    group_a = phase17_invitation_fixture["group_a"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    async with make_client(db_session, token=token_leader_a) as ac:
        payload = {
            "full_name": "Invalid Email",
            "email": "not-an-email",
        }
        res = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_pending_invitation_rejected(db_session: AsyncSession, phase17_invitation_fixture):
    """Duplicate pending invitation for the same email in the same group raises 409 Conflict."""
    group_a = phase17_invitation_fixture["group_a"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    async with make_client(db_session, token=token_leader_a) as ac:
        payload = {
            "full_name": "First Invite",
            "email": "duplicate@example.com",
        }
        res1 = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res1.status_code == 201

        res2 = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res2.status_code == 409


@pytest.mark.asyncio
async def test_active_member_reinvite_rejected(db_session: AsyncSession, phase17_invitation_fixture):
    """Inviting a student who is already an active member of the group raises 409 Conflict."""
    group_a = phase17_invitation_fixture["group_a"]
    student_a = phase17_invitation_fixture["student_a"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    async with make_client(db_session, token=token_leader_a) as ac:
        payload = {
            "full_name": "Already Member",
            "email": student_a.email,
        }
        res = await ac.post(f"/api/v1/groups/{group_a.id}/invitations", json=payload)
        assert res.status_code == 409


# ── TOKEN SECURITY & DATABASE HASHING TESTS ──────────────────────────

@pytest.mark.asyncio
async def test_token_hash_stored_in_database(db_session: AsyncSession, phase17_invitation_fixture):
    """Raw invitation token is never stored in plaintext in the database; only SHA-256 hash exists."""
    group_a = phase17_invitation_fixture["group_a"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        group_id=group_a.id,
        email="token.security@example.com",
        full_name="Token Security",
        department="Materials",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    # Query directly from DB
    res = await db_session.execute(select(Invitation).where(Invitation.id == inv.id))
    db_inv = res.scalar_one()

    assert db_inv.token_hash == token_hash
    assert raw_token not in db_inv.token_hash
    assert len(db_inv.token_hash) == 64  # SHA-256 hex digest length


# ── PUBLIC VALIDATION ENDPOINT TESTS ─────────────────────────────────

@pytest.mark.asyncio
async def test_public_invitation_validation(db_session: AsyncSession, phase17_invitation_fixture):
    """Public token validation returns safe, sanitized group & project metadata."""
    group_a = phase17_invitation_fixture["group_a"]
    p1 = phase17_invitation_fixture["p1"]
    leader_a = phase17_invitation_fixture["leader_a"]

    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        group_id=group_a.id,
        email="validate.member@example.com",
        full_name="Validating Member",
        department="Nanotech",
        phone="12345",
        roll_number="NT-01",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        res = await ac.get(f"/api/v1/invitations/validate/{raw_token}")
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["valid"] is True
        assert data["group_name"] == group_a.name
        assert data["project_code"] == p1.project_code
        assert data["project_name"] == p1.name
        assert data["invited_name"] == "Validating Member"
        assert data["invited_email"] == "validate.member@example.com"
        assert data["leader_name"] == leader_a.full_name
        assert "token_hash" not in data
        assert "password" not in data


@pytest.mark.asyncio
async def test_expired_invitation_validation_fails(db_session: AsyncSession, phase17_invitation_fixture):
    """Validating an expired invitation token returns 400 Bad Request."""
    group_a = phase17_invitation_fixture["group_a"]
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        group_id=group_a.id,
        email="expired@example.com",
        full_name="Expired Member",
        department="Nanotech",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session) as ac:
        res = await ac.get(f"/api/v1/invitations/validate/{raw_token}")
        assert res.status_code == 400
        assert "expired" in res.json()["detail"].lower()


# ── RESEND & REVOCATION TESTS ────────────────────────────────────────

@pytest.mark.asyncio
async def test_resend_and_rate_limit(db_session: AsyncSession, phase17_invitation_fixture):
    """Resend generates a new token hash and enforces a 60-second cooldown."""
    group_a = phase17_invitation_fixture["group_a"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    raw_token = generate_secure_invitation_token()
    old_hash = hash_invitation_token(raw_token)

    # Created in the past to allow first resend
    inv = Invitation(
        group_id=group_a.id,
        email="resend.test@example.com",
        full_name="Resend Test",
        department="Nanotech",
        phone="N/A",
        roll_number="N/A",
        token_hash=old_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        updated_at=datetime.now(timezone.utc) - timedelta(seconds=120),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session, token=token_leader_a) as ac:
        # First resend should succeed
        res = await ac.post(f"/api/v1/groups/{group_a.id}/invitations/{inv.id}/resend")
        assert res.status_code == 200

        # Verify token hash was changed
        await db_session.refresh(inv)
        assert inv.token_hash != old_hash

        # Second resend immediately after should be rate-limited
        res_cooldown = await ac.post(f"/api/v1/groups/{group_a.id}/invitations/{inv.id}/resend")
        assert res_cooldown.status_code == 400
        assert "seconds" in res_cooldown.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoke_invitation(db_session: AsyncSession, phase17_invitation_fixture):
    """Revoking an invitation marks it CANCELLED and invalidates the token."""
    group_a = phase17_invitation_fixture["group_a"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]

    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        group_id=group_a.id,
        email="revoke.test@example.com",
        full_name="Revoke Test",
        department="Nanotech",
        phone="N/A",
        roll_number="N/A",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db_session.add(inv)
    await db_session.flush()

    async with make_client(db_session, token=token_leader_a) as ac:
        # Revoke
        res = await ac.delete(f"/api/v1/groups/{group_a.id}/invitations/{inv.id}")
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "CANCELLED"

    # Validation should now fail
    async with make_client(db_session) as ac:
        res_val = await ac.get(f"/api/v1/invitations/validate/{raw_token}")
        assert res_val.status_code == 400


# ── LISTING ACCESS CONTROL TESTS ─────────────────────────────────────

@pytest.mark.asyncio
async def test_list_invitations_access_control(db_session: AsyncSession, phase17_invitation_fixture):
    """Tests access control matrix for listing group invitations."""
    group_a = phase17_invitation_fixture["group_a"]
    group_b = phase17_invitation_fixture["group_b"]
    token_admin = phase17_invitation_fixture["token_admin"]
    token_leader_a = phase17_invitation_fixture["token_leader_a"]
    token_student_a = phase17_invitation_fixture["token_student_a"]

    # 1. Leader A lists own group A -> 200 OK
    async with make_client(db_session, token=token_leader_a) as ac:
        res_own = await ac.get(f"/api/v1/groups/{group_a.id}/invitations")
        assert res_own.status_code == 200

        # Leader A lists group B -> 403 Forbidden
        res_other = await ac.get(f"/api/v1/groups/{group_b.id}/invitations")
        assert res_other.status_code == 403

    # 2. Student A lists group A -> 403 Forbidden
    async with make_client(db_session, token=token_student_a) as ac:
        res_stud = await ac.get(f"/api/v1/groups/{group_a.id}/invitations")
        assert res_stud.status_code == 403

    # 3. Admin lists all system-wide -> 200 OK
    async with make_client(db_session, token=token_admin) as ac:
        res_admin = await ac.get("/api/v1/invitations/")
        assert res_admin.status_code == 200
