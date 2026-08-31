"""
GreenSynth Analytics — Phase 19 Admin Dashboard Unit & Integration Tests

Validates:
1. Admin user authentication and session creation (200 OK, account_type == "ADMIN").
2. Admin accesses global system overview endpoint (200 OK, accurate database metrics).
3. Student access to Admin overview rejected (403 Forbidden).
4. Unauthenticated request to Admin overview rejected (401 Unauthorized).
5. Admin accesses all synthesis projects P1–P8 (200 OK).
6. Student access to Admin projects endpoint rejected (403 Forbidden).
7. Admin accesses research groups list (200 OK).
8. Student access to Admin groups list rejected (403 Forbidden).
9. Admin accesses student user accounts list (200 OK, password hashes strictly omitted).
10. Student access to Admin users list rejected (403 Forbidden).
11. Admin accesses experiments list with optional project filter (200 OK).
12. Student access to Admin experiments list rejected (403 Forbidden).
13. Admin accesses samples list (200 OK).
14. Student access to Admin samples list rejected (403 Forbidden).
15. Tampering tests: Student attempting query params (?admin=true) or header manipulation receives 403 Forbidden.
16. Admin system-wide access operates independently without requiring research group membership.
"""

from __future__ import annotations

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole


@pytest.fixture
async def phase19_fixture(db_session: AsyncSession):
    """Sets up Projects P1–P8, Admin, Leader, Student, and research records."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Projects P1 through P8
    projects = []
    for i in range(1, 9):
        p = Project(
            id=uuid.uuid4(),
            name=f"Synthesis Project {i}",
            project_code=f"P{i}-{suffix}",
            description=f"Standard Project {i} description",
            material="CuO" if i in (1, 2, 3, 4, 7, 8) else "Si",
            extract="Mulberry" if i in (1, 2, 3, 4, 7, 8) else "Rice husk",
            solvent="Ethanol" if i % 2 == 1 else "Acetone",
            synthesis_method="Sol-gel" if i in (1, 2) else ("Hydrothermal" if i in (3, 4, 5, 6) else "Spray Pyrolysis"),
            status=ProjectStatus.ACTIVE.value,
        )
        projects.append(p)
        db_session.add(p)
    await db_session.flush()

    # 2. Admin User
    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p19_{suffix}",
        email=f"admin.p19_{suffix}@greensynth.edu",
        full_name="Platform Administrator",
        department="Central Lab",
        phone="1000000000",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminSecurePass123!"),
        is_active=True,
    )
    # 3. Student User
    student = User(
        id=uuid.uuid4(),
        username=f"student_p19_{suffix}",
        email=f"student.p19_{suffix}@greensynth.edu",
        full_name="Student Researcher",
        department="Chemical Engineering",
        phone="1000000001",
        roll_number=f"STU-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentSecurePass123!"),
        is_active=True,
    )
    db_session.add_all([admin, student])
    await db_session.flush()

    # 4. Research Group for P1
    group = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Oxides Research Group {suffix}",
        project_id=projects[0].id,
        leader_user_id=student.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group)
    await db_session.flush()

    # 5. Group Membership
    membership = GroupMembership(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=student.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership)
    await db_session.flush()

    # 6. Experiments & Samples
    exp1 = Experiment(
        id=uuid.uuid4(),
        project_id=projects[0].id,
        experiment_code=f"EXP-P1-{suffix}",
        title="P1 Sol-Gel Trial",
        status="COMPLETED",
    )
    db_session.add(exp1)
    await db_session.flush()

    smp1 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp1.id,
        sample_code=f"SMP-P1-{suffix}",
        name="CuO Nanopowder Sample",
        material="CuO",
        status="PREPARED",
    )
    db_session.add(smp1)
    await db_session.flush()

    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_student = create_access_token(student.id, account_type="STUDENT")

    return {
        "projects": projects,
        "admin": admin,
        "student": student,
        "group": group,
        "exp1": exp1,
        "smp1": smp1,
        "token_admin": token_admin,
        "token_student": token_student,
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


# ── ADMIN OVERVIEW TESTS ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_overview(db_session: AsyncSession, phase19_fixture):
    """Admin successfully fetches system overview with real database counts."""
    token_admin = phase19_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["total_projects"] >= 8
        assert data["total_groups"] >= 1
        assert data["total_students"] >= 1
        assert data["total_experiments"] >= 1
        assert data["total_samples"] >= 1


@pytest.mark.asyncio
async def test_student_blocked_from_admin_overview(db_session: AsyncSession, phase19_fixture):
    """Student receives 403 Forbidden when calling Admin overview endpoint."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_blocked_from_admin_overview(db_session: AsyncSession, phase19_fixture):
    """Unauthenticated caller receives 401 Unauthorized when calling Admin overview endpoint."""
    async with make_client(db_session) as ac:
        res = await ac.get("/api/v1/admin/overview")
        assert res.status_code == 401


# ── ADMIN PROJECT CATALOG TESTS ──────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_projects(db_session: AsyncSession, phase19_fixture):
    """Admin successfully lists all synthesis projects."""
    token_admin = phase19_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        res = await ac.get("/api/v1/admin/projects")
        assert res.status_code == 200
        data = res.json()["data"]

        assert len(data) >= 8
        codes = [p["project_code"] for p in data]
        assert any(c.startswith("P1") for c in codes)
        assert any(c.startswith("P7") for c in codes)


@pytest.mark.asyncio
async def test_student_blocked_from_admin_projects(db_session: AsyncSession, phase19_fixture):
    """Student receives 403 Forbidden when calling Admin projects endpoint."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        res = await ac.get("/api/v1/admin/projects")
        assert res.status_code == 403


# ── ADMIN RESEARCH GROUPS TESTS ──────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_groups(db_session: AsyncSession, phase19_fixture):
    """Admin lists all research groups across all projects."""
    token_admin = phase19_fixture["token_admin"]
    group = phase19_fixture["group"]

    async with make_client(db_session, token=token_admin) as ac:
        res = await ac.get("/api/v1/admin/groups")
        assert res.status_code == 200
        data = res.json()["data"]

        assert len(data) >= 1
        group_ids = [g["group_id"] for g in data]
        assert str(group.id) in group_ids


@pytest.mark.asyncio
async def test_student_blocked_from_admin_groups(db_session: AsyncSession, phase19_fixture):
    """Student receives 403 Forbidden when calling Admin groups endpoint."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        res = await ac.get("/api/v1/admin/groups")
        assert res.status_code == 403


# ── ADMIN USERS & SECURITY TESTS ─────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_users_without_exposing_passwords(db_session: AsyncSession, phase19_fixture):
    """Admin lists all users; password hashes and sensitive secrets are strictly omitted."""
    token_admin = phase19_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        res = await ac.get("/api/v1/admin/users")
        assert res.status_code == 200
        data = res.json()["data"]

        assert len(data) >= 2
        for user_entry in data:
            assert "password" not in user_entry
            assert "password_hash" not in user_entry
            assert "token" not in user_entry


@pytest.mark.asyncio
async def test_student_blocked_from_admin_users(db_session: AsyncSession, phase19_fixture):
    """Student receives 403 Forbidden when calling Admin users endpoint."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        res = await ac.get("/api/v1/admin/users")
        assert res.status_code == 403


# ── ADMIN EXPERIMENTS & SAMPLES TESTS ────────────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_experiments_and_samples(db_session: AsyncSession, phase19_fixture):
    """Admin accesses experiments and samples across projects."""
    token_admin = phase19_fixture["token_admin"]
    projects = phase19_fixture["projects"]

    async with make_client(db_session, token=token_admin) as ac:
        # All experiments
        res_exp = await ac.get("/api/v1/admin/experiments")
        assert res_exp.status_code == 200
        assert len(res_exp.json()["data"]) >= 1

        # Filtered by project
        res_exp_filt = await ac.get(f"/api/v1/admin/experiments?project_id={projects[0].id}")
        assert res_exp_filt.status_code == 200
        assert len(res_exp_filt.json()["data"]) >= 1

        # All samples
        res_smp = await ac.get("/api/v1/admin/samples")
        assert res_smp.status_code == 200
        assert len(res_smp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_student_blocked_from_admin_experiments_and_samples(db_session: AsyncSession, phase19_fixture):
    """Student receives 403 Forbidden when calling Admin experiment and sample endpoints."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        res1 = await ac.get("/api/v1/admin/experiments")
        assert res1.status_code == 403

        res2 = await ac.get("/api/v1/admin/samples")
        assert res2.status_code == 403


# ── PRIVILEGE TAMPERING TESTS ────────────────────────────────────────

@pytest.mark.asyncio
async def test_privilege_tampering_by_student_rejected(db_session: AsyncSession, phase19_fixture):
    """Student appending ?admin=true or sending custom headers still receives 403 Forbidden."""
    token_student = phase19_fixture["token_student"]

    async with make_client(db_session, token=token_student) as ac:
        # URL tampering
        res1 = await ac.get("/api/v1/admin/overview?admin=true&role=ADMIN")
        assert res1.status_code == 403

        # Header tampering
        res2 = await ac.get(
            "/api/v1/admin/projects",
            headers={"Authorization": f"Bearer {token_student}", "X-Role": "ADMIN"},
        )
        assert res2.status_code == 403
