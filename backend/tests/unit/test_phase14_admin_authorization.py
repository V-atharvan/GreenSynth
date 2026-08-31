"""
GreenSynth Analytics — Phase 14 Admin Authorization Tests

Validates:
1. require_admin centralized dependency enforcement.
2. Authenticated Admin access to all Admin endpoints (/api/v1/admin/*) -> 200 OK.
3. Authenticated Student rejection from Admin endpoints -> 403 Forbidden.
4. Unauthenticated access rejection -> 401 Unauthorized.
5. Inactive Admin and expired/invalid JWT rejection -> 401 Unauthorized.
6. Admin authorization is NOT email-based (account_type is the sole authority).
7. Privilege escalation prevention (body, query params, headers cannot elevate student).
8. Admin does NOT require group membership or project assignment to access system-wide resources.
9. Admin overview, projects, groups, users, experiments, and samples listings.
10. Idempotent Admin seeding and secure password hash verification.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.api.deps import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database.seed import seed_admin_user
from app.main import app
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def admin_auth_fixture(db_session: AsyncSession):
    """Sets up projects P1 through P8, an Admin user, a Student user, and an alternate Admin."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Create P1 and P8
    p1 = Project(
        id=uuid.uuid4(),
        project_code="P1-TEST",
        name="Project 1 CuO Sol-Gel",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Sol-Gel",
        status="ACTIVE",
    )
    p8 = Project(
        id=uuid.uuid4(),
        project_code="P8-TEST",
        name="Project 8 CuO Spray Pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Acetone",
        synthesis_method="Spray Pyrolysis",
        status="ACTIVE",
    )
    db_session.add_all([p1, p8])
    await db_session.flush()

    # 2. Primary Admin user (v.atharvan@gmail.com)
    res_admin = await db_session.execute(select(User).where(User.email == "v.atharvan@gmail.com"))
    admin_user = res_admin.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
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
        db_session.add(admin_user)
        await db_session.flush()

    # 3. Alternate Admin user with a completely different email
    custom_admin = User(
        id=uuid.uuid4(),
        username=f"admin_custom_{suffix}",
        email=f"custom_admin_{suffix}@greensynth.edu",
        full_name="Secondary Admin",
        department="Platform Ops",
        phone="9876543219",
        roll_number=f"ADM-CUST-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("custom_admin_pass"),
        is_active=True,
    )
    db_session.add(custom_admin)

    # 4. Active Student user
    student_user = User(
        id=uuid.uuid4(),
        username=f"student_p14_{suffix}",
        email=f"student_p14_{suffix}@greensynth.edu",
        full_name="Student Phase14",
        department="Chemistry",
        phone="9876543211",
        roll_number=f"ROLL-P14-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("student_secret_pass"),
        is_active=True,
    )
    db_session.add(student_user)

    # 5. Inactive Admin user
    inactive_admin = User(
        id=uuid.uuid4(),
        username=f"admin_inact_{suffix}",
        email=f"admin_inactive_{suffix}@greensynth.edu",
        full_name="Inactive Admin",
        department="Platform Ops",
        phone="9876543218",
        roll_number=f"ADM-INACT-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("inactive_admin_pass"),
        is_active=False,
    )
    db_session.add(inactive_admin)
    await db_session.flush()

    # Create Experiment and Sample for testing
    exp = Experiment(
        id=uuid.uuid4(),
        project_id=p1.id,
        experiment_code=f"EXP-P14-{suffix}",
        title="Admin Test Experiment",
        status="IN_PROGRESS",
    )
    db_session.add(exp)
    await db_session.flush()

    sample = Sample(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        sample_code=f"SMP-P14-{suffix}",
        name="Admin Test Sample",
        material="CuO",
        status="PREPARED",
    )
    db_session.add(sample)
    await db_session.flush()

    # Generate JWTs
    admin_token = create_access_token(admin_user.id, account_type="ADMIN")
    custom_admin_token = create_access_token(custom_admin.id, account_type="ADMIN")
    student_token = create_access_token(student_user.id, account_type="STUDENT")
    inactive_admin_token = create_access_token(inactive_admin.id, account_type="ADMIN")

    return {
        "p1": p1,
        "p8": p8,
        "admin_user": admin_user,
        "admin_token": admin_token,
        "custom_admin": custom_admin,
        "custom_admin_token": custom_admin_token,
        "student_user": student_user,
        "student_token": student_token,
        "inactive_admin": inactive_admin,
        "inactive_admin_token": inactive_admin_token,
        "exp": exp,
        "sample": sample,
    }


def make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
        follow_redirects=True,
    )


# ── TEST 1: AUTHENTICATED ADMIN ACCESSES ADMIN ENDPOINTS ─────────────

@pytest.mark.asyncio
async def test_admin_accesses_admin_overview(db_session: AsyncSession, admin_auth_fixture):
    """Admin GET /api/v1/admin/overview returns 200 OK and valid system metrics."""
    async with make_client(db_session, token=admin_auth_fixture["admin_token"]) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        assert "total_projects" in data
        assert "total_students" in data
        assert "total_experiments" in data
        assert "total_samples" in data
        assert data["total_projects"] >= 2


# ── TEST 2: AUTHENTICATED STUDENT ACCESS REJECTED WITH 403 ───────────

@pytest.mark.asyncio
async def test_student_rejected_from_admin_endpoints(db_session: AsyncSession, admin_auth_fixture):
    """Student attempting Admin-only endpoints receives HTTP 403 Forbidden."""
    async with make_client(db_session, token=admin_auth_fixture["student_token"]) as ac:
        # Overview
        res_overview = await ac.get("/api/v1/admin/overview")
        assert res_overview.status_code == 403
        assert "ADMIN_REQUIRED" in res_overview.text

        # Projects Admin
        res_proj = await ac.get("/api/v1/admin/projects")
        assert res_proj.status_code == 403

        # Groups Admin
        res_grp = await ac.get("/api/v1/admin/groups")
        assert res_grp.status_code == 403

        # Users Admin
        res_usr = await ac.get("/api/v1/admin/users")
        assert res_usr.status_code == 403


# ── TEST 3: UNAUTHENTICATED ACCESS REJECTED WITH 401 ──────────────────

@pytest.mark.asyncio
async def test_unauthenticated_rejected_from_admin_endpoints(db_session: AsyncSession):
    """Unauthenticated user accessing Admin endpoint receives HTTP 401 Unauthorized."""
    async with make_client(db_session) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 401


# ── TEST 4: ADMIN ACCESSES SYSTEM-WIDE RESOURCES (P1 TO P8) ──────────

@pytest.mark.asyncio
async def test_admin_accesses_all_projects_without_group_or_assignment(db_session: AsyncSession, admin_auth_fixture):
    """Admin has direct access to P1 and P8 without needing group or project membership."""
    p1 = admin_auth_fixture["p1"]
    p8 = admin_auth_fixture["p8"]

    async with make_client(db_session, token=admin_auth_fixture["admin_token"]) as ac:
        res_p1 = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res_p1.status_code == 200

        res_p8 = await ac.get(f"/api/v1/projects/{p8.id}")
        assert res_p8.status_code == 200

        res_admin_proj = await ac.get("/api/v1/admin/projects")
        assert res_admin_proj.status_code == 200
        p_ids = [p["id"] for p in res_admin_proj.json()["data"]]
        assert str(p1.id) in p_ids
        assert str(p8.id) in p_ids


# ── TEST 5: ADMIN EXPERIMENT & SAMPLE LISTINGS ───────────────────────

@pytest.mark.asyncio
async def test_admin_experiments_and_samples_access(db_session: AsyncSession, admin_auth_fixture):
    """Admin retrieves experiments and samples system-wide with optional filters."""
    p1 = admin_auth_fixture["p1"]
    exp = admin_auth_fixture["exp"]

    async with make_client(db_session, token=admin_auth_fixture["admin_token"]) as ac:
        # All experiments
        res_exp = await ac.get("/api/v1/admin/experiments")
        assert res_exp.status_code == 200
        assert len(res_exp.json()["data"]) >= 1

        # Filter by project_id
        res_exp_filter = await ac.get(f"/api/v1/admin/experiments?project_id={p1.id}")
        assert res_exp_filter.status_code == 200
        assert len(res_exp_filter.json()["data"]) >= 1

        # All samples
        res_smp = await ac.get(f"/api/v1/admin/samples?experiment_id={exp.id}")
        assert res_smp.status_code == 200
        assert len(res_smp.json()["data"]) >= 1


# ── TEST 6: INVALID & EXPIRED JWT REJECTION ──────────────────────────

@pytest.mark.asyncio
async def test_invalid_and_expired_jwt_rejected(db_session: AsyncSession, admin_auth_fixture):
    """Tampered signature or expired JWT rejected with HTTP 401."""
    settings = get_settings()
    admin_id = admin_auth_fixture["admin_user"].id

    # Expired token
    expired_token = create_access_token(admin_id, account_type="ADMIN", expires_delta=timedelta(seconds=-10))
    async with make_client(db_session, token=expired_token) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 401

    # Tampered signature
    tampered_token = jwt.encode(
        {"sub": str(admin_id), "type": "access", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        "rogue-secret-key-123",
        algorithm="HS256",
    )
    async with make_client(db_session, token=tampered_token) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 401


# ── TEST 7: INACTIVE ADMIN REJECTION ─────────────────────────────────

@pytest.mark.asyncio
async def test_inactive_admin_rejected(db_session: AsyncSession, admin_auth_fixture):
    """Deactivated Admin account is rejected with HTTP 401."""
    async with make_client(db_session, token=admin_auth_fixture["inactive_admin_token"]) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 401


# ── TEST 8: AUTHORIZATION IS NOT EMAIL-BASED ─────────────────────────

@pytest.mark.asyncio
async def test_authorization_is_not_email_based(db_session: AsyncSession, admin_auth_fixture):
    """User with account_type=ADMIN and a non-admin email is authorized; account_type=STUDENT is blocked."""
    # 1. Custom Admin with different email -> Allowed (200)
    async with make_client(db_session, token=admin_auth_fixture["custom_admin_token"]) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 200

    # 2. Student -> Blocked (403)
    async with make_client(db_session, token=admin_auth_fixture["student_token"]) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 403


# ── TEST 9: PRIVILEGE ESCALATION PREVENTION ──────────────────────────

@pytest.mark.asyncio
async def test_privilege_escalation_blocked(db_session: AsyncSession, admin_auth_fixture):
    """Query parameters, headers, or request payload cannot elevate a Student to Admin."""
    async with make_client(db_session, token=admin_auth_fixture["student_token"]) as ac:
        # Query parameter ?admin=true
        res_q1 = await ac.get("/api/v1/admin/overview?admin=true")
        assert res_q1.status_code == 403

        # Query parameter ?role=ADMIN
        res_q2 = await ac.get("/api/v1/admin/overview?role=ADMIN")
        assert res_q2.status_code == 403

        # Header X-Admin: true
        ac.headers["X-Admin"] = "true"
        res_h = await ac.get("/api/v1/admin/overview")
        assert res_h.status_code == 403


# ── TEST 10: ADMIN PASSWORD & IDEMPOTENT SEED VERIFICATION ───────────

@pytest.mark.asyncio
async def test_admin_seed_idempotency_and_password_storage(db_session: AsyncSession):
    """Admin seeding is idempotent and never stores plaintext passwords."""
    await seed_admin_user(db_session)
    await seed_admin_user(db_session)  # Run twice

    res = await db_session.execute(select(User).where(User.email == "v.atharvan@gmail.com"))
    admin_users = res.scalars().all()
    assert len(admin_users) == 1
    admin = admin_users[0]

    assert admin.account_type == "ADMIN"
    assert admin.is_admin is True
    assert admin.is_active is True
    # Verify password_hash is hashed and does not contain plaintext 'aaaaaaaa'
    assert admin.password_hash.startswith("$pbkdf2-sha256$") or admin.password_hash.startswith("$2b$")
    assert "aaaaaaaa" != admin.password_hash
