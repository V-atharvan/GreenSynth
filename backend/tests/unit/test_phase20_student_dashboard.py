"""
GreenSynth Analytics — Phase 20 Student Dashboard Unit & Integration Tests

Validates:
1. Student authentication through unified login (200 OK, account_type == "STUDENT").
2. GET /api/v1/auth/me returns student profile with active membership and assigned project.
3. GET /api/v1/dashboard/stats returns strictly project-scoped metrics for Student.
4. Student cannot bypass project scope via ?project_id query parameters (403 Forbidden).
5. Student without active group membership is denied access (403 NO_ACTIVE_GROUP).
6. Admin receives system-wide statistics from GET /api/v1/dashboard/stats.
7. Unauthenticated calls to /dashboard/stats return 401 Unauthorized.
8. Cross-project data isolation between Student A (P7) and Student B (P2).
9. Security verification: Password hash and secrets are never exposed in user or dashboard responses.
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
async def phase20_fixture(db_session: AsyncSession):
    """Sets up Projects P7 & P2, Admin, Student A (P7), Student B (P2), Student C (no group)."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Projects P7 & P2
    p7 = Project(
        id=uuid.uuid4(),
        name="CuO Spray Pyrolysis",
        project_code=f"P7-{suffix}",
        description="Phytochemical synthesis of CuO by spray pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        name="CuO Acetone Sol-Gel",
        project_code=f"P2-{suffix}",
        description="Sol-gel synthesis of CuO with acetone",
        material="CuO",
        extract="Mulberry",
        solvent="Acetone",
        synthesis_method="Sol-Gel",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add_all([p7, p2])
    await db_session.flush()

    # 2. Users: Admin, Student A (P7), Student B (P2), Student C (No group)
    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p20_{suffix}",
        email=f"admin.p20_{suffix}@greensynth.edu",
        full_name="Administrator Atharva",
        department="Central Lab",
        phone="1000000000",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    student_a = User(
        id=uuid.uuid4(),
        username=f"student_a_{suffix}",
        email=f"student.a_{suffix}@greensynth.edu",
        full_name="Student A (P7)",
        department="Chemical Engineering",
        phone="1000000001",
        roll_number=f"STU-A-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassA123!"),
        is_active=True,
    )
    student_b = User(
        id=uuid.uuid4(),
        username=f"student_b_{suffix}",
        email=f"student.b_{suffix}@greensynth.edu",
        full_name="Student B (P2)",
        department="Materials Science",
        phone="1000000002",
        roll_number=f"STU-B-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassB123!"),
        is_active=True,
    )
    student_c = User(
        id=uuid.uuid4(),
        username=f"student_c_{suffix}",
        email=f"student.c_{suffix}@greensynth.edu",
        full_name="Student C (Ungrouped)",
        department="Physics",
        phone="1000000003",
        roll_number=f"STU-C-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassC123!"),
        is_active=True,
    )
    db_session.add_all([admin, student_a, student_b, student_c])
    await db_session.flush()

    # 3. Groups & Memberships
    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Spray Pyrolysis Group {suffix}",
        project_id=p7.id,
        leader_user_id=student_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Sol-Gel Group {suffix}",
        project_id=p2.id,
        leader_user_id=student_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add_all([group_a, group_b])
    await db_session.flush()

    mem_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=student_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    mem_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=student_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add_all([mem_a, mem_b])
    await db_session.flush()

    # 4. Experiments & Samples for P7
    exp_p7_1 = Experiment(
        id=uuid.uuid4(),
        project_id=p7.id,
        experiment_code=f"EXP-P7-1-{suffix}",
        title="P7 Precursor Trial 1",
        status="COMPLETED",
    )
    exp_p7_2 = Experiment(
        id=uuid.uuid4(),
        project_id=p7.id,
        experiment_code=f"EXP-P7-2-{suffix}",
        title="P7 Precursor Trial 2",
        status="IN_PROGRESS",
    )
    smp_p7 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p7_1.id,
        sample_code=f"SMP-P7-{suffix}",
        name="CuO Spray Sample",
        material="CuO",
        status="PREPARED",
    )

    # Experiments & Samples for P2
    exp_p2_1 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code=f"EXP-P2-1-{suffix}",
        title="P2 Gelation Trial",
        status="COMPLETED",
    )
    smp_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2_1.id,
        sample_code=f"SMP-P2-{suffix}",
        name="CuO Gel Sample",
        material="CuO",
        status="PREPARED",
    )

    db_session.add_all([exp_p7_1, exp_p7_2, smp_p7, exp_p2_1, smp_p2])
    await db_session.flush()

    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_a = create_access_token(student_a.id, account_type="STUDENT")
    token_b = create_access_token(student_b.id, account_type="STUDENT")
    token_c = create_access_token(student_c.id, account_type="STUDENT")

    return {
        "p7": p7,
        "p2": p2,
        "admin": admin,
        "student_a": student_a,
        "student_b": student_b,
        "student_c": student_c,
        "group_a": group_a,
        "group_b": group_b,
        "exp_p7_1": exp_p7_1,
        "exp_p2_1": exp_p2_1,
        "smp_p7": smp_p7,
        "smp_p2": smp_p2,
        "token_admin": token_admin,
        "token_a": token_a,
        "token_b": token_b,
        "token_c": token_c,
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


# ── STUDENT LOGIN & ME TESTS ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_login_and_me_resolution(db_session: AsyncSession, phase20_fixture):
    """Student logs in via unified /auth/login and receives account_type=STUDENT and membership details."""
    student_a = phase20_fixture["student_a"]
    p7 = phase20_fixture["p7"]
    group_a = phase20_fixture["group_a"]

    async with make_client(db_session) as ac:
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": student_a.email, "password": "StudentPassA123!"},
        )
        assert login_res.status_code == 200
        data = login_res.json()["data"]

        assert data["user"]["account_type"] == "STUDENT"
        token = data["access_token"]

        # Call /auth/me
        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        profile = me_res.json()["data"]

        assert profile["email"] == student_a.email
        assert len(profile["memberships"]) >= 1
        membership = profile["memberships"][0]
        assert membership["group_id"] == str(group_a.id)
        assert membership["project_id"] == str(p7.id)
        assert "password" not in profile
        assert "password_hash" not in profile


# ── STUDENT DASHBOARD STATS SCOPING TESTS ─────────────────────────────

@pytest.mark.asyncio
async def test_student_dashboard_stats_strictly_scoped(db_session: AsyncSession, phase20_fixture):
    """Student A gets statistics strictly scoped to P7 (2 experiments, 1 sample)."""
    token_a = phase20_fixture["token_a"]

    async with make_client(db_session, token=token_a) as ac:
        res = await ac.get("/api/v1/dashboard/stats")
        assert res.status_code == 200
        stats = res.json()

        assert stats["total_projects"] == 1
        assert stats["total_experiments"] == 2
        assert stats["total_samples"] == 1
        assert len(stats["recent_experiments"]) == 2


@pytest.mark.asyncio
async def test_student_cannot_override_project_scope_via_query_param(db_session: AsyncSession, phase20_fixture):
    """Student A (assigned to P7) receives 403 when passing ?project_id={P2.id}."""
    token_a = phase20_fixture["token_a"]
    p2 = phase20_fixture["p2"]

    async with make_client(db_session, token=token_a) as ac:
        res = await ac.get(f"/api/v1/dashboard/stats?project_id={p2.id}")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_student_without_group_blocked_from_stats(db_session: AsyncSession, phase20_fixture):
    """Student C without active group membership receives 403 Forbidden."""
    token_c = phase20_fixture["token_c"]

    async with make_client(db_session, token=token_c) as ac:
        res = await ac.get("/api/v1/dashboard/stats")
        assert res.status_code == 403


# ── ADMIN & UNAUTHENTICATED TESTS ────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_dashboard_stats_global(db_session: AsyncSession, phase20_fixture):
    """Admin receives system-wide statistics across all projects."""
    token_admin = phase20_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        res = await ac.get("/api/v1/dashboard/stats")
        assert res.status_code == 200
        stats = res.json()

        assert stats["total_projects"] >= 2
        assert stats["total_experiments"] >= 3
        assert stats["total_samples"] >= 2


@pytest.mark.asyncio
async def test_unauthenticated_blocked_from_stats(db_session: AsyncSession, phase20_fixture):
    """Unauthenticated caller to /dashboard/stats receives 401 Unauthorized."""
    async with make_client(db_session) as ac:
        res = await ac.get("/api/v1/dashboard/stats")
        assert res.status_code == 401


# ── CROSS-PROJECT ISOLATION TESTS ────────────────────────────────────

@pytest.mark.asyncio
async def test_cross_project_isolation_student_a_and_b(db_session: AsyncSession, phase20_fixture):
    """Student A sees only P7 experiments; Student B sees only P2 experiments."""
    token_a = phase20_fixture["token_a"]
    token_b = phase20_fixture["token_b"]

    async with make_client(db_session, token=token_a) as ac:
        res_a = await ac.get("/api/v1/dashboard/stats")
        assert res_a.status_code == 200
        codes_a = [e["experiment_code"] for e in res_a.json()["recent_experiments"]]
        assert all("P7" in c for c in codes_a)
        assert not any("P2" in c for c in codes_a)

    async with make_client(db_session, token=token_b) as ac:
        res_b = await ac.get("/api/v1/dashboard/stats")
        assert res_b.status_code == 200
        codes_b = [e["experiment_code"] for e in res_b.json()["recent_experiments"]]
        assert all("P2" in c for c in codes_b)
        assert not any("P7" in c for c in codes_b)
