"""
GreenSynth Analytics — Settings & Profile API Integration Tests
Tests:
  - GET /api/v1/auth/me (authenticated user profile retrieval)
  - PATCH /api/v1/auth/me (permitted profile update)
  - POST /api/v1/auth/change-password (secure password change with verification)
  - PATCH /api/v1/admin/users/{user_id}/status (Admin user activation/deactivation)
  - Authorization isolation (Student cannot toggle user status or promote accounts)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.user import User, UserRole


import uuid

@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    p_code = f"P_{uuid.uuid4().hex[:6]}"
    proj = Project(
        project_code=p_code,
        name="CuO + Mulberry Extract + Ethanol + Spray Pyrolysis",
        material="CuO",
        extract="Mulberry Extract",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)
    return proj


@pytest.fixture
async def student_user(db_session: AsyncSession) -> User:
    uid = uuid.uuid4().hex[:8]
    user = User(
        username=f"student_{uid}",
        email=f"student_{uid}@greensynth.org",
        password_hash=hash_password("InitialPassword123!"),
        full_name="Student Tester",
        department="Chemical Engineering",
        phone="+91 9876543210",
        roll_number=f"STU-{uid[:4]}",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    uid = uuid.uuid4().hex[:8]
    admin = User(
        username=f"admin_{uid}",
        email=f"admin_{uid}@greensynth.org",
        password_hash=hash_password("AdminSecurePass123!"),
        full_name="Admin Tester",
        department="Administration",
        phone="+91 9999999999",
        roll_number=f"ADM-{uid[:4]}",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.mark.asyncio
async def test_get_me_returns_profile_without_password_hash(
    client: AsyncClient, student_user: User
):
    token = create_access_token(student_user.id, account_type="STUDENT")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["email"] == student_user.email
    assert body["data"]["full_name"] == "Student Tester"
    assert body["data"]["account_type"] == "STUDENT"
    # Never expose password_hash
    assert "password_hash" not in body["data"]
    assert "password" not in body["data"]


@pytest.mark.asyncio
async def test_update_me_permitted_fields_only(
    client: AsyncClient, student_user: User, db_session: AsyncSession
):
    token = create_access_token(student_user.id, account_type="STUDENT")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Updated Student Name",
        "department": "Nanotechnology",
        "phone": "+91 9123456789",
        "roll_number": "NANO-2026-99",
    }

    res = await client.patch("/api/v1/auth/me", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["full_name"] == "Updated Student Name"
    assert data["department"] == "Nanotechnology"
    assert data["phone"] == "+91 9123456789"
    assert data["roll_number"] == "NANO-2026-99"

    # Verify immutable fields remain unchanged
    assert data["email"] == student_user.email
    assert data["account_type"] == "STUDENT"


@pytest.mark.asyncio
async def test_change_password_flow(
    client: AsyncClient, student_user: User, db_session: AsyncSession
):
    token = create_access_token(student_user.id, account_type="STUDENT")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Reject invalid current password
    bad_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongPassword!",
            "new_password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        },
        headers=headers,
    )
    assert bad_res.status_code == 400
    assert "Current password is incorrect" in bad_res.json()["detail"]

    # 2. Reject password mismatch
    mismatch_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "InitialPassword123!",
            "new_password": "BrandNewPassword123!",
            "confirm_password": "DifferentPassword123!",
        },
        headers=headers,
    )
    assert mismatch_res.status_code == 400

    # 3. Successful password change
    good_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "InitialPassword123!",
            "new_password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        },
        headers=headers,
    )
    assert good_res.status_code == 200
    assert good_res.json()["message"] == "Password changed successfully."

    # 4. Verify password in DB has been updated
    await db_session.refresh(student_user)
    assert verify_password("BrandNewPassword123!", student_user.password_hash)


@pytest.mark.asyncio
async def test_admin_can_toggle_user_status(
    client: AsyncClient, admin_user: User, student_user: User, db_session: AsyncSession
):
    admin_token = create_access_token(admin_user.id, account_type="ADMIN")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Active student cannot access admin endpoints (Forbidden 403)
    active_student_token = create_access_token(student_user.id, account_type="STUDENT")
    active_student_headers = {"Authorization": f"Bearer {active_student_token}"}

    forbidden_res = await client.patch(
        f"/api/v1/admin/users/{student_user.id}/status",
        json={"is_active": False},
        headers=active_student_headers,
    )
    assert forbidden_res.status_code == 403

    # Admin deactivates student
    deact_res = await client.patch(
        f"/api/v1/admin/users/{student_user.id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["is_active"] is False

    await db_session.refresh(student_user)
    assert student_user.is_active is False

    # Deactivated student account receives 401 Unauthorized
    inactive_res = await client.get("/api/v1/auth/me", headers=active_student_headers)
    assert inactive_res.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_request_to_me_returns_401(unauthenticated_client: AsyncClient):
    res = await unauthenticated_client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_retrieves_me_profile(client: AsyncClient, admin_user: User):
    token = create_access_token(admin_user.id, account_type="ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["account_type"] == "ADMIN"
    assert data["email"] == admin_user.email
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_admin_updates_own_full_name(client: AsyncClient, admin_user: User, db_session: AsyncSession):
    token = create_access_token(admin_user.id, account_type="ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.patch("/api/v1/auth/me", json={"full_name": "Atharva Vaddepalli"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "Atharva Vaddepalli"

    await db_session.refresh(admin_user)
    assert admin_user.full_name == "Atharva Vaddepalli"


@pytest.mark.asyncio
async def test_student_cannot_elevate_privilege_or_change_security_fields(
    client: AsyncClient, student_user: User, db_session: AsyncSession
):
    token = create_access_token(student_user.id, account_type="STUDENT")
    headers = {"Authorization": f"Bearer {token}"}

    # Malicious attempt to change account_type, is_active, and email
    malicious_payload = {
        "full_name": "Rahul Updated",
        "account_type": "ADMIN",
        "role": "ADMIN",
        "is_active": False,
        "email": "hacked@greensynth.org",
        "id": "00000000-0000-0000-0000-000000000000",
    }

    res = await client.patch("/api/v1/auth/me", json=malicious_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Name is updated safely
    assert data["full_name"] == "Rahul Updated"

    # Security fields remain strictly unchanged
    assert data["account_type"] == "STUDENT"
    assert data["email"] == student_user.email
    assert data["is_active"] is True
    assert data["id"] == str(student_user.id)

    await db_session.refresh(student_user)
    assert student_user.role == UserRole.STUDENT
    assert student_user.account_type == "STUDENT"
    assert student_user.email == data["email"]



