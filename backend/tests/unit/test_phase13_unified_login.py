"""
GreenSynth Analytics — Phase 13 Unified Login System Integration & Security Tests

Validates:
1. EXACTLY ONE unified login endpoint: POST /api/v1/auth/login.
2. Admin login with v.atharvan@gmail.com / aaaaaaaa succeeds and returns account_type="ADMIN".
3. Student login with valid credentials succeeds and returns account_type="STUDENT".
4. Login requires ONLY {"email", "password"} — ignores any extra frontend fields.
5. Role/Account-type tampering immunity:
   - Submitting account_type="STUDENT" for Admin remains ADMIN.
   - Submitting account_type="ADMIN" or is_admin=True for Student remains STUDENT.
6. Generic error handling for wrong password, unknown email, and inactive user (HTTP 401).
7. Email normalization (whitespace trimming and case insensitivity).
8. Strict exclusion of password_hash and sensitive secrets from all responses.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.api.deps import get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def unified_login_users(db_session: AsyncSession):
    """Sets up an Admin user, an active Student user, and an inactive user."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Admin user
    res_admin = await db_session.execute(select(User).where(User.email == "v.atharvan@gmail.com"))
    admin = res_admin.scalar_one_or_none()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            username=f"admin_atharva_{suffix}",
            email="v.atharvan@gmail.com",
            full_name="Atharvan V (Admin)",
            department="Chemical Engineering",
            phone="9876543210",
            roll_number="ADMIN-001",
            role=UserRole.ADMIN,
            password_hash=hash_password("aaaaaaaa"),
            is_active=True,
        )
        db_session.add(admin)
        await db_session.flush()

    # 2. Active Student user
    student = User(
        id=uuid.uuid4(),
        username=f"student_u13_{suffix}",
        email=f"student13_{suffix}@greensynth.edu",
        full_name="Student Phase13",
        department="Chemistry",
        phone="9876543211",
        roll_number=f"ROLL-P13-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("student_pass_123"),
        is_active=True,
    )
    db_session.add(student)

    # 3. Inactive Student user
    inactive_student = User(
        id=uuid.uuid4(),
        username=f"student_inact13_{suffix}",
        email=f"inactive13_{suffix}@greensynth.edu",
        full_name="Inactive Student Phase13",
        department="Physics",
        phone="9876543212",
        roll_number=f"ROLL-INACT-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("inactive_pass_123"),
        is_active=False,
    )
    db_session.add(inactive_student)
    await db_session.flush()

    return {
        "admin": admin,
        "student": student,
        "inactive_student": inactive_student,
    }


def make_client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    )


# ── 1. UNIFIED LOGIN: ADMIN AUTHENTICATION ───────────────────────────

@pytest.mark.asyncio
async def test_admin_login_success(db_session: AsyncSession, unified_login_users):
    """Admin authenticates via POST /api/v1/auth/login and receives account_type=ADMIN."""
    async with make_client(db_session) as ac:
        res = await ac.post("/api/v1/auth/login", json={
            "email": "v.atharvan@gmail.com",
            "password": "aaaaaaaa",
        })
        assert res.status_code == 200, res.text
        data = res.json()["data"]

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "v.atharvan@gmail.com"
        assert data["user"]["account_type"] == "ADMIN"
        assert data["user"]["role"] == "ADMIN"
        assert data["user"]["is_active"] is True
        assert "password_hash" not in res.text
        assert "password" not in data["user"]


# ── 2. UNIFIED LOGIN: STUDENT AUTHENTICATION ─────────────────────────

@pytest.mark.asyncio
async def test_student_login_success(db_session: AsyncSession, unified_login_users):
    """Student authenticates via the exact SAME endpoint and receives account_type=STUDENT."""
    student = unified_login_users["student"]
    async with make_client(db_session) as ac:
        res = await ac.post("/api/v1/auth/login", json={
            "email": student.email,
            "password": "student_pass_123",
        })
        assert res.status_code == 200, res.text
        data = res.json()["data"]

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == student.email
        assert data["user"]["account_type"] == "STUDENT"
        assert data["user"]["is_active"] is True
        assert "password_hash" not in res.text


# ── 3. NO ROLE PARAMETER REQUIREMENT ─────────────────────────────────

@pytest.mark.asyncio
async def test_login_requires_only_email_and_password(db_session: AsyncSession, unified_login_users):
    """Login payload only requires email and password; no role or account_type parameters."""
    student = unified_login_users["student"]
    async with make_client(db_session) as ac:
        payload = {"email": student.email, "password": "student_pass_123"}
        res = await ac.post("/api/v1/auth/login", json=payload)
        assert res.status_code == 200
        assert res.json()["data"]["user"]["id"] == str(student.id)


# ── 4. ROLE TAMPERING IMMUNITY ───────────────────────────────────────

@pytest.mark.asyncio
async def test_client_cannot_override_account_type(db_session: AsyncSession, unified_login_users):
    """Client cannot escalate or downgrade privileges via request body or query params."""
    student = unified_login_users["student"]

    async with make_client(db_session) as ac:
        # Student attempts to claim ADMIN in payload
        res_student_hack = await ac.post("/api/v1/auth/login", json={
            "email": student.email,
            "password": "student_pass_123",
            "account_type": "ADMIN",
            "role": "ADMIN",
            "is_admin": True,
        })
        assert res_student_hack.status_code == 200
        # Backend authoritatively forces STUDENT from DB
        assert res_student_hack.json()["data"]["user"]["account_type"] == "STUDENT"

        # Admin with spoofed STUDENT payload remains ADMIN
        res_admin = await ac.post("/api/v1/auth/login", json={
            "email": "v.atharvan@gmail.com",
            "password": "aaaaaaaa",
            "account_type": "STUDENT",
        })
        assert res_admin.status_code == 200
        assert res_admin.json()["data"]["user"]["account_type"] == "ADMIN"


# ── 5. GENERIC LOGIN FAILURES ────────────────────────────────────────

@pytest.mark.asyncio
async def test_wrong_admin_password_generic_error(db_session: AsyncSession, unified_login_users):
    """Wrong admin password returns generic 401 without revealing account existence."""
    async with make_client(db_session) as ac:
        res = await ac.post("/api/v1/auth/login", json={
            "email": "v.atharvan@gmail.com",
            "password": "wrong_password_attempt",
        })
        assert res.status_code == 401
        assert "Invalid email or password" in res.text


@pytest.mark.asyncio
async def test_nonexistent_email_generic_error(db_session: AsyncSession):
    """Non-existent email returns identical generic 401."""
    async with make_client(db_session) as ac:
        res = await ac.post("/api/v1/auth/login", json={
            "email": "nonexistent_researcher@greensynth.edu",
            "password": "any_password",
        })
        assert res.status_code == 401
        assert "Invalid email or password" in res.text


@pytest.mark.asyncio
async def test_inactive_user_login_rejected(db_session: AsyncSession, unified_login_users):
    """Deactivated account cannot login and returns 401."""
    inactive = unified_login_users["inactive_student"]
    async with make_client(db_session) as ac:
        res = await ac.post("/api/v1/auth/login", json={
            "email": inactive.email,
            "password": "inactive_pass_123",
        })
        assert res.status_code == 401


# ── 6. EMAIL NORMALIZATION ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_email_normalization_on_login(db_session: AsyncSession, unified_login_users):
    """Whitespace padding and uppercase casing are normalized automatically."""
    async with make_client(db_session) as ac:
        # Uppercase + whitespace Admin login
        res_admin = await ac.post("/api/v1/auth/login", json={
            "email": "  V.ATHARVAN@GMAIL.COM  ",
            "password": "aaaaaaaa",
        })
        assert res_admin.status_code == 200
        assert res_admin.json()["data"]["user"]["account_type"] == "ADMIN"
