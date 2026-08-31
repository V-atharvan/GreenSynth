"""
GreenSynth Analytics — Integration Tests: Authentication Endpoints

Tests API routes:
  - POST /api/v1/auth/register-leader
  - POST /api/v1/auth/login
  - POST /api/v1/auth/accept-invitation
  - GET  /api/v1/auth/me
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_invitation_token
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User

AUTH_API = "/api/v1/auth"


@pytest.fixture
async def seeded_project(db_session: AsyncSession) -> Project:
    """Create an active project for testing leader registration."""
    proj = Project(
        project_code=f"P7-AUTH-{uuid.uuid4().hex[:6].upper()}",
        name="Auth Integration Test Project",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.flush()
    return proj


# ── Leader Registration API Tests ───────────────────────────

@pytest.mark.asyncio
async def test_register_leader_endpoint_success(
    client: AsyncClient, seeded_project: Project
) -> None:
    """POST /auth/register-leader creates leader, group, membership, and returns JWT."""
    payload = {
        "full_name": "Test Group Leader",
        "department": "Chemical Engineering",
        "phone": "9998887776",
        "password": "LeaderPassword123!",
        "project_id": str(seeded_project.id),
        "roll_number": "CHEM-LEADER-01",
        "email": "leader_endpoint@greensynth.edu",
        "group_name": "P7 Endpoint Group",
    }
    response = await client.post(f"{AUTH_API}/register-leader", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert "data" in body
    data = body["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert "user" in data

    user = data["user"]
    assert user["email"] == "leader_endpoint@greensynth.edu"
    assert user["full_name"] == "Test Group Leader"
    assert user["roll_number"] == "CHEM-LEADER-01"
    assert user["is_active"] is True
    assert "password_hash" not in user
    assert "password" not in user


@pytest.mark.asyncio
async def test_register_leader_duplicate_email_fails(
    client: AsyncClient, seeded_project: Project
) -> None:
    """POST /auth/register-leader with duplicate email returns 409 Conflict."""
    payload = {
        "full_name": "Original Leader",
        "department": "CSE",
        "phone": "1234567890",
        "password": "Password123!",
        "project_id": str(seeded_project.id),
        "roll_number": "CSE-DUP-1",
        "email": "duplicate_check@greensynth.edu",
    }
    res1 = await client.post(f"{AUTH_API}/register-leader", json=payload)
    assert res1.status_code == 201

    res2 = await client.post(f"{AUTH_API}/register-leader", json=payload)
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_register_leader_invalid_project_fails(
    client: AsyncClient,
) -> None:
    """POST /auth/register-leader with non-existent project returns 400 Bad Request."""
    payload = {
        "full_name": "Orphan Leader",
        "department": "CSE",
        "phone": "1234567890",
        "password": "Password123!",
        "project_id": str(uuid.uuid4()),
        "roll_number": "CSE-NO-PROJ",
        "email": "orphan_leader@greensynth.edu",
    }
    response = await client.post(f"{AUTH_API}/register-leader", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_leader_short_password_fails(
    client: AsyncClient, seeded_project: Project
) -> None:
    """POST /auth/register-leader with password < 8 chars returns 422 Unprocessable Content."""
    payload = {
        "full_name": "Short Pass User",
        "department": "CSE",
        "phone": "1234567890",
        "password": "short",
        "project_id": str(seeded_project.id),
        "roll_number": "CSE-SHORT",
        "email": "short_pass@greensynth.edu",
    }
    response = await client.post(f"{AUTH_API}/register-leader", json=payload)
    assert response.status_code == 422


# ── Login API Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_endpoint_success(
    client: AsyncClient, seeded_project: Project
) -> None:
    """POST /auth/login returns JWT on valid credentials."""
    reg_payload = {
        "full_name": "Login User",
        "department": "ENTC",
        "phone": "9991112223",
        "password": "SecurePassword123!",
        "project_id": str(seeded_project.id),
        "roll_number": "ENTC-LOGIN-1",
        "email": "login_user@greensynth.edu",
    }
    await client.post(f"{AUTH_API}/register-leader", json=reg_payload)

    # Login
    login_payload = {
        "email": "  LOGIN_USER@greensynth.edu  ",
        "password": "SecurePassword123!",
    }
    response = await client.post(f"{AUTH_API}/login", json=login_payload)
    assert response.status_code == 200

    body = response.json()
    assert "data" in body
    assert "access_token" in body["data"]
    assert body["data"]["user"]["email"] == "login_user@greensynth.edu"
    assert "password_hash" not in body["data"]["user"]


@pytest.mark.asyncio
async def test_login_wrong_password_fails(
    client: AsyncClient, seeded_project: Project
) -> None:
    """POST /auth/login returns generic 401 on wrong password."""
    reg_payload = {
        "full_name": "Wrong Pass User",
        "department": "ENTC",
        "phone": "9991112224",
        "password": "CorrectPassword123!",
        "project_id": str(seeded_project.id),
        "roll_number": "ENTC-WRONG-1",
        "email": "wrong_pass_user@greensynth.edu",
    }
    await client.post(f"{AUTH_API}/register-leader", json=reg_payload)

    response = await client.post(
        f"{AUTH_API}/login",
        json={"email": "wrong_pass_user@greensynth.edu", "password": "BadPassword123!"},
    )
    assert response.status_code == 401
    detail_msg = response.json().get("detail", response.json().get("message", ""))
    assert "invalid email or password" in detail_msg.lower()


@pytest.mark.asyncio
async def test_login_unknown_email_fails(client: AsyncClient) -> None:
    """POST /auth/login returns generic 401 on nonexistent user."""
    response = await client.post(
        f"{AUTH_API}/login",
        json={"email": "unknown_email@greensynth.edu", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    detail_msg = response.json().get("detail", response.json().get("message", ""))
    assert "invalid email or password" in detail_msg.lower()


# ── Accept Invitation API Tests ─────────────────────────────

@pytest.mark.asyncio
async def test_accept_invitation_endpoint_success(
    client: AsyncClient, db_session: AsyncSession, seeded_project: Project
) -> None:
    """POST /auth/accept-invitation validates token, sets password, and activates member."""
    # 1. Register leader
    reg_payload = {
        "full_name": "Inv Group Leader",
        "department": "Mechanical",
        "phone": "5555555555",
        "password": "LeaderPassword123!",
        "project_id": str(seeded_project.id),
        "roll_number": "MECH-001",
        "email": "inv_leader@greensynth.edu",
    }
    leader_res = await client.post(f"{AUTH_API}/register-leader", json=reg_payload)
    leader_id = leader_res.json()["data"]["user"]["id"]

    # 2. Get created group
    from sqlalchemy import select
    grp_res = await db_session.execute(
        select(ResearchGroup).where(ResearchGroup.leader_user_id == uuid.UUID(leader_id))
    )
    group = grp_res.scalar_one()

    # 3. Create invitation
    raw_token = "valid_api_invitation_token_999"
    inv = Invitation(
        group_id=group.id,
        email="invited_endpoint@greensynth.edu",
        full_name="Invited Endpoint Student",
        department="Mechanical",
        phone="4444444444",
        roll_number="MECH-002",
        token_hash=hash_invitation_token(raw_token),
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(inv)
    await db_session.flush()

    # 4. Accept invitation via API
    accept_payload = {
        "token": raw_token,
        "password": "MemberEndpointPass123!",
    }
    response = await client.post(f"{AUTH_API}/accept-invitation", json=accept_payload)
    assert response.status_code == 200

    data = response.json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == "invited_endpoint@greensynth.edu"
    assert data["user"]["full_name"] == "Invited Endpoint Student"
    assert data["user"]["roll_number"] == "MECH-002"


@pytest.mark.asyncio
async def test_accept_invitation_invalid_token_fails(client: AsyncClient) -> None:
    """POST /auth/accept-invitation with invalid token returns 400."""
    response = await client.post(
        f"{AUTH_API}/accept-invitation",
        json={"token": "completely_fake_token", "password": "Password123!"},
    )
    assert response.status_code == 400


# ── GET /auth/me API Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(
    client: AsyncClient, seeded_project: Project
) -> None:
    """GET /auth/me returns authenticated user details and memberships with Bearer token."""
    reg_payload = {
        "full_name": "Me Endpoint User",
        "department": "Civil Engineering",
        "phone": "6666666666",
        "password": "Password123!",
        "project_id": str(seeded_project.id),
        "roll_number": "CIVIL-001",
        "email": "me_endpoint@greensynth.edu",
        "group_name": "Green Building Materials Unit",
    }
    reg_res = await client.post(f"{AUTH_API}/register-leader", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]

    response = await client.get(
        f"{AUTH_API}/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    body = response.json()
    assert "data" in body
    profile = body["data"]
    assert profile["email"] == "me_endpoint@greensynth.edu"
    assert profile["full_name"] == "Me Endpoint User"
    assert len(profile["memberships"]) == 1
    assert profile["memberships"][0]["group_name"] == "Green Building Materials Unit"
    assert profile["memberships"][0]["is_leader"] is True
    assert profile["memberships"][0]["project_code"] == seeded_project.project_code
    assert "password_hash" not in profile


@pytest.mark.asyncio
async def test_get_me_no_auth_header_fails(unauthenticated_client: AsyncClient) -> None:
    """GET /auth/me without Authorization header returns 401 Unauthorized."""
    response = await unauthenticated_client.get(f"{AUTH_API}/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token_fails(client: AsyncClient) -> None:
    """GET /auth/me with bogus Bearer token returns 401 Unauthorized."""
    response = await client.get(
        f"{AUTH_API}/me",
        headers={"Authorization": "Bearer invalid.bogus.jwt.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /auth/me with expired token returns 401 Unauthorized."""
    user = User(
        username="expired_jwt_user",
        email="expired_jwt@greensynth.edu",
        full_name="Expired User",
        department="CSE",
        phone="0000000000",
        roll_number="EXP-001",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()

    expired_token = create_access_token(user.id, expires_delta=timedelta(seconds=-10))

    response = await client.get(
        f"{AUTH_API}/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
