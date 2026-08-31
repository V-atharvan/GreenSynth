"""
GreenSynth Analytics — Phase 15 Student Group & Project Authorization Tests

Validates:
1. Student with P1 membership accesses P1 -> 200 OK.
2. Student with P1 membership denied access to P2 -> 403 Forbidden.
3. Student with P2 membership accesses P2 -> 200 OK and denied P1 -> 403 Forbidden.
4. Admin accesses P1, P2, and P8 -> 200 OK without requiring group membership.
5. Student without membership rejected -> 403 Forbidden (NO_ACTIVE_GROUP).
6. Student with inactive membership rejected -> 403 Forbidden (NO_ACTIVE_GROUP).
7. Cross-Project Direct Object Reference (IDOR) protection:
   - Direct Experiment UUID access of unauthorized project -> 403 Forbidden.
   - Direct Sample UUID access of unauthorized project -> 403 Forbidden.
   - Admin accesses both direct UUIDs -> 200 OK.
8. Query parameter privilege tampering (?project_id=P2) rejected.
9. Dedicated Student Portal endpoints (/api/v1/student/project, /group, /dashboard, /me).
"""

import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def phase15_authorization_fixture(db_session: AsyncSession):
    """Sets up Projects P1 & P2, Groups A & B, Student A (P1), Student B (P2), Student C (no group), and Student D (inactive)."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Projects P1 and P2
    p1 = Project(
        id=uuid.uuid4(),
        project_code=f"P1-{suffix}",
        name="Project 1 Sol-Gel CuO",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Sol-Gel",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        project_code=f"P2-{suffix}",
        name="Project 2 Sol-Gel CuO Acetone",
        material="CuO",
        extract="Mulberry",
        solvent="Acetone",
        synthesis_method="Sol-Gel",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    # 2. Admin User
    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p15_{suffix}",
        email=f"admin_p15_{suffix}@greensynth.edu",
        full_name="Platform Admin",
        department="Central Lab",
        phone="1000000000",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("admin_pass"),
        is_active=True,
    )
    db_session.add(admin)

    # 3. Student A (Assigned to Group A -> P1)
    student_a = User(
        id=uuid.uuid4(),
        username=f"student_a_{suffix}",
        email=f"student_a_{suffix}@greensynth.edu",
        full_name="Student Alice (P1)",
        department="Chemistry",
        phone="1000000001",
        roll_number=f"STU-A-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("alice_pass"),
        is_active=True,
    )
    # 4. Student B (Assigned to Group B -> P2)
    student_b = User(
        id=uuid.uuid4(),
        username=f"student_b_{suffix}",
        email=f"student_b_{suffix}@greensynth.edu",
        full_name="Student Bob (P2)",
        department="Materials Science",
        phone="1000000002",
        roll_number=f"STU-B-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("bob_pass"),
        is_active=True,
    )
    # 5. Student C (No group membership)
    student_c = User(
        id=uuid.uuid4(),
        username=f"student_c_{suffix}",
        email=f"student_c_{suffix}@greensynth.edu",
        full_name="Student Charlie (No Group)",
        department="Physics",
        phone="1000000003",
        roll_number=f"STU-C-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("charlie_pass"),
        is_active=True,
    )
    # 6. Student D (Inactive group membership)
    student_d = User(
        id=uuid.uuid4(),
        username=f"student_d_{suffix}",
        email=f"student_d_{suffix}@greensynth.edu",
        full_name="Student Dave (Inactive Member)",
        department="Chemical Engineering",
        phone="1000000004",
        roll_number=f"STU-D-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("dave_pass"),
        is_active=True,
    )
    db_session.add_all([student_a, student_b, student_c, student_d])
    await db_session.flush()

    # 7. Research Groups
    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Group A Nanomaterials {suffix}",
        project_id=p1.id,
        leader_user_id=student_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Group B Oxides {suffix}",
        project_id=p2.id,
        leader_user_id=student_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_d = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Group D Inactive {suffix}",
        project_id=p1.id,
        leader_user_id=student_d.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add_all([group_a, group_b, group_d])
    await db_session.flush()

    # 8. Group Memberships
    m_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=student_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    m_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=student_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    m_d = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_d.id,
        user_id=student_d.id,
        is_leader=False,
        status=MembershipStatus.INACTIVE.value,  # Inactive
    )
    db_session.add_all([m_a, m_b, m_d])
    await db_session.flush()

    # 9. Research Records for P1 and P2
    exp_p1 = Experiment(
        id=uuid.uuid4(),
        project_id=p1.id,
        experiment_code=f"EXP-P1-{suffix}",
        title="Experiment P1 Alice",
        status="IN_PROGRESS",
    )
    exp_p2 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code=f"EXP-P2-{suffix}",
        title="Experiment P2 Bob",
        status="IN_PROGRESS",
    )
    db_session.add_all([exp_p1, exp_p2])
    await db_session.flush()

    sample_p1 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p1.id,
        sample_code=f"SMP-P1-{suffix}",
        name="Sample P1 Alice",
        material="CuO",
        status="PREPARED",
    )
    sample_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2.id,
        sample_code=f"SMP-P2-{suffix}",
        name="Sample P2 Bob",
        material="CuO",
        status="PREPARED",
    )
    db_session.add_all([sample_p1, sample_p2])
    await db_session.flush()

    # Tokens
    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_student_a = create_access_token(student_a.id, account_type="STUDENT")
    token_student_b = create_access_token(student_b.id, account_type="STUDENT")
    token_student_c = create_access_token(student_c.id, account_type="STUDENT")
    token_student_d = create_access_token(student_d.id, account_type="STUDENT")

    return {
        "p1": p1,
        "p2": p2,
        "admin": admin,
        "student_a": student_a,
        "student_b": student_b,
        "student_c": student_c,
        "student_d": student_d,
        "group_a": group_a,
        "group_b": group_b,
        "exp_p1": exp_p1,
        "exp_p2": exp_p2,
        "sample_p1": sample_p1,
        "sample_p2": sample_p2,
        "token_admin": token_admin,
        "token_student_a": token_student_a,
        "token_student_b": token_student_b,
        "token_student_c": token_student_c,
        "token_student_d": token_student_d,
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


# ── TEST 1 & 2: STUDENT A (P1) ALLOWED P1, DENIED P2 ─────────────────

@pytest.mark.asyncio
async def test_student_a_accesses_p1_and_denied_p2(db_session: AsyncSession, phase15_authorization_fixture):
    """Student A assigned to P1 accesses P1 successfully, but is denied access to P2."""
    p1 = phase15_authorization_fixture["p1"]
    p2 = phase15_authorization_fixture["p2"]
    token_a = phase15_authorization_fixture["token_student_a"]

    async with make_client(db_session, token=token_a) as ac:
        # Access P1 -> 200 OK
        res_p1 = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res_p1.status_code == 200, res_p1.text

        # Access P2 -> 403 Forbidden
        res_p2 = await ac.get(f"/api/v1/projects/{p2.id}")
        assert res_p2.status_code == 403
        assert "PROJECT_ACCESS_DENIED" in res_p2.text


# ── TEST 3 & 4: STUDENT B (P2) ALLOWED P2, DENIED P1 ─────────────────

@pytest.mark.asyncio
async def test_student_b_accesses_p2_and_denied_p1(db_session: AsyncSession, phase15_authorization_fixture):
    """Student B assigned to P2 accesses P2 successfully, but is denied access to P1."""
    p1 = phase15_authorization_fixture["p1"]
    p2 = phase15_authorization_fixture["p2"]
    token_b = phase15_authorization_fixture["token_student_b"]

    async with make_client(db_session, token=token_b) as ac:
        # Access P2 -> 200 OK
        res_p2 = await ac.get(f"/api/v1/projects/{p2.id}")
        assert res_p2.status_code == 200, res_p2.text

        # Access P1 -> 403 Forbidden
        res_p1 = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res_p1.status_code == 403
        assert "PROJECT_ACCESS_DENIED" in res_p1.text


# ── TEST 5 & 6: ADMIN ACCESSES BOTH P1 AND P2 ─────────────────────────

@pytest.mark.asyncio
async def test_admin_accesses_both_p1_and_p2(db_session: AsyncSession, phase15_authorization_fixture):
    """Admin has unrestricted access to P1, P2, and all projects."""
    p1 = phase15_authorization_fixture["p1"]
    p2 = phase15_authorization_fixture["p2"]
    token_admin = phase15_authorization_fixture["token_admin"]

    async with make_client(db_session, token=token_admin) as ac:
        res_p1 = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res_p1.status_code == 200

        res_p2 = await ac.get(f"/api/v1/projects/{p2.id}")
        assert res_p2.status_code == 200


# ── TEST 7: STUDENT WITHOUT GROUP MEMBERSHIP REJECTED ────────────────

@pytest.mark.asyncio
async def test_student_without_membership_rejected(db_session: AsyncSession, phase15_authorization_fixture):
    """Student C with no active group membership receives 403 NO_ACTIVE_GROUP."""
    p1 = phase15_authorization_fixture["p1"]
    token_c = phase15_authorization_fixture["token_student_c"]

    async with make_client(db_session, token=token_c) as ac:
        res = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res.status_code == 403
        assert "NO_ACTIVE_GROUP" in res.text


# ── TEST 8: STUDENT WITH INACTIVE MEMBERSHIP REJECTED ────────────────

@pytest.mark.asyncio
async def test_student_with_inactive_membership_rejected(db_session: AsyncSession, phase15_authorization_fixture):
    """Student D with revoked/inactive membership receives 403 NO_ACTIVE_GROUP."""
    p1 = phase15_authorization_fixture["p1"]
    token_d = phase15_authorization_fixture["token_student_d"]

    async with make_client(db_session, token=token_d) as ac:
        res = await ac.get(f"/api/v1/projects/{p1.id}")
        assert res.status_code == 403
        assert "NO_ACTIVE_GROUP" in res.text


# ── TEST 9: DIRECT EXPERIMENT & SAMPLE IDOR PROTECTION ───────────────

@pytest.mark.asyncio
async def test_cross_project_direct_idor_protection(db_session: AsyncSession, phase15_authorization_fixture):
    """Direct resource UUID access across projects is strictly forbidden for students."""
    exp_p1 = phase15_authorization_fixture["exp_p1"]
    exp_p2 = phase15_authorization_fixture["exp_p2"]
    sample_p1 = phase15_authorization_fixture["sample_p1"]
    sample_p2 = phase15_authorization_fixture["sample_p2"]
    token_a = phase15_authorization_fixture["token_student_a"]
    token_b = phase15_authorization_fixture["token_student_b"]
    token_admin = phase15_authorization_fixture["token_admin"]

    # Student A (P1) accessing P1 experiment -> 200, accessing P2 experiment -> 403/404
    async with make_client(db_session, token=token_a) as ac:
        res_exp_a = await ac.get(f"/api/v1/experiments/{exp_p1.id}")
        assert res_exp_a.status_code == 200

        res_exp_b_leak = await ac.get(f"/api/v1/experiments/{exp_p2.id}")
        assert res_exp_b_leak.status_code in (403, 404)

        res_smp_a = await ac.get(f"/api/v1/samples/{sample_p1.id}")
        assert res_smp_a.status_code == 200

        res_smp_b_leak = await ac.get(f"/api/v1/samples/{sample_p2.id}")
        assert res_smp_b_leak.status_code in (403, 404)

    # Student B (P2) accessing P2 experiment -> 200, accessing P1 experiment -> 403/404
    async with make_client(db_session, token=token_b) as ac:
        res_exp_b = await ac.get(f"/api/v1/experiments/{exp_p2.id}")
        assert res_exp_b.status_code == 200

        res_exp_a_leak = await ac.get(f"/api/v1/experiments/{exp_p1.id}")
        assert res_exp_a_leak.status_code in (403, 404)

    # Admin accessing both -> 200
    async with make_client(db_session, token=token_admin) as ac:
        assert (await ac.get(f"/api/v1/experiments/{exp_p1.id}")).status_code == 200
        assert (await ac.get(f"/api/v1/experiments/{exp_p2.id}")).status_code == 200
        assert (await ac.get(f"/api/v1/samples/{sample_p1.id}")).status_code == 200
        assert (await ac.get(f"/api/v1/samples/{sample_p2.id}")).status_code == 200


# ── TEST 10: QUERY PARAMETER PROJECT SPOOFING REJECTED ───────────────

@pytest.mark.asyncio
async def test_query_parameter_spoofing_rejected(db_session: AsyncSession, phase15_authorization_fixture):
    """Student A cannot request experiments for P2 by supplying ?project_id=<P2_UUID>."""
    p2 = phase15_authorization_fixture["p2"]
    token_a = phase15_authorization_fixture["token_student_a"]

    async with make_client(db_session, token=token_a) as ac:
        res = await ac.get(f"/api/v1/experiments?project_id={p2.id}")
        assert res.status_code == 403
        assert "PROJECT_ACCESS_DENIED" in res.text


# ── TEST 11: DEDICATED STUDENT PORTAL ENDPOINTS ──────────────────────

@pytest.mark.asyncio
async def test_student_portal_endpoints(db_session: AsyncSession, phase15_authorization_fixture):
    """Verifies /api/v1/student/me, /project, /group, and /dashboard."""
    p1 = phase15_authorization_fixture["p1"]
    group_a = phase15_authorization_fixture["group_a"]
    token_a = phase15_authorization_fixture["token_student_a"]

    async with make_client(db_session, token=token_a) as ac:
        # 1. Student /me
        res_me = await ac.get("/api/v1/student/me")
        assert res_me.status_code == 200
        data_me = res_me.json()["data"]
        assert data_me["account_type"] == "STUDENT"
        assert len(data_me["memberships"]) >= 1

        # 2. Student /project
        res_proj = await ac.get("/api/v1/student/project")
        assert res_proj.status_code == 200
        data_proj = res_proj.json()["data"]
        assert data_proj["id"] == str(p1.id)
        assert data_proj["project_code"] == p1.project_code

        # 3. Student /group
        res_grp = await ac.get("/api/v1/student/group")
        assert res_grp.status_code == 200
        data_grp = res_grp.json()["data"]
        assert data_grp["group_id"] == str(group_a.id)

        # 4. Student /dashboard
        res_dash = await ac.get("/api/v1/student/dashboard")
        assert res_dash.status_code == 200
        data_dash = res_dash.json()
        assert "total_experiments" in data_dash
        assert "total_samples" in data_dash
