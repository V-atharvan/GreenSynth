"""
GreenSynth Analytics — Phase 21 Research API Authorization Unit & Integration Tests

Validates:
1. Unauthenticated requests to research endpoints receive HTTP 401 Unauthorized.
2. System Administrator receives global system-wide research access across all active projects (P1–P8).
3. Student Researcher is strictly constrained to the project assigned through active group membership.
4. Cross-project direct ID access protection (IDOR defense: returns 404/403 for unauthorized project entities).
5. Cross-project write protection (POST/PUT/DELETE rejected for unauthorized projects).
6. Query parameter tamper immunity (?project_id={OTHER_PROJECT} returns 403 Forbidden).
7. Student without active group membership receives 403 NO_ACTIVE_GROUP.
8. Scoped research domains: Experiments, Samples, Reports, ML Datasets, DOE Objectives, Optimization, Recommendations.
"""

from __future__ import annotations

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
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
async def phase21_fixture(db_session: AsyncSession):
    """Sets up Projects P7 & P2, Admin, Student A (P7), Student B (P2), and Ungrouped Student C."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Projects P7 & P2
    p7 = Project(
        id=uuid.uuid4(),
        name="CuO Spray Pyrolysis P7",
        project_code=f"P7-{suffix}",
        description="Phytochemical synthesis of CuO via spray pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        name="CuO Sol-Gel Acetone P2",
        project_code=f"P2-{suffix}",
        description="Sol-gel synthesis of CuO via acetone",
        material="CuO",
        extract="Mulberry",
        solvent="Acetone",
        synthesis_method="Sol-Gel",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add_all([p7, p2])
    await db_session.flush()

    # 2. Users
    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p21_{suffix}",
        email=f"admin.p21_{suffix}@greensynth.edu",
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
        username=f"student_p21_a_{suffix}",
        email=f"student.p21_a_{suffix}@greensynth.edu",
        full_name="Student Researcher A (P7)",
        department="Chemical Engineering",
        phone="1000000001",
        roll_number=f"STU-A-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassA123!"),
        is_active=True,
    )
    student_b = User(
        id=uuid.uuid4(),
        username=f"student_p21_b_{suffix}",
        email=f"student.p21_b_{suffix}@greensynth.edu",
        full_name="Student Researcher B (P2)",
        department="Materials Science",
        phone="1000000002",
        roll_number=f"STU-B-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassB123!"),
        is_active=True,
    )
    student_c = User(
        id=uuid.uuid4(),
        username=f"student_p21_c_{suffix}",
        email=f"student.p21_c_{suffix}@greensynth.edu",
        full_name="Ungrouped Student C",
        department="Physics",
        phone="1000000003",
        roll_number=f"STU-C-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassC123!"),
        is_active=True,
    )
    db_session.add_all([admin, student_a, student_b, student_c])
    await db_session.flush()

    # 3. Research Groups & Memberships
    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Spray Pyrolysis Research Group {suffix}",
        project_id=p7.id,
        leader_user_id=student_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Sol-Gel Research Group {suffix}",
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

    # 4. Research Data: Experiments & Samples for P7
    exp_p7 = Experiment(
        id=uuid.uuid4(),
        project_id=p7.id,
        experiment_code=f"EXP-P7-VAL-{suffix}",
        title="P7 Spray Pyrolysis Thin Film",
        status="COMPLETED",
    )
    smp_p7 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p7.id,
        sample_code=f"SMP-P7-VAL-{suffix}",
        name="CuO Spray Substrate",
        material="CuO",
        status="PREPARED",
    )

    # Experiments & Samples for P2
    exp_p2 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code=f"EXP-P2-VAL-{suffix}",
        title="P2 Sol-Gel Gelation",
        status="COMPLETED",
    )
    smp_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2.id,
        sample_code=f"SMP-P2-VAL-{suffix}",
        name="CuO Xerogel Monolith",
        material="CuO",
        status="PREPARED",
    )

    db_session.add_all([exp_p7, smp_p7, exp_p2, smp_p2])
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
        "exp_p7": exp_p7,
        "exp_p2": exp_p2,
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
        follow_redirects=True,
    )


# ── TEST 1: UNAUTHENTICATED CALLS REJECTED (401) ──────────────────────

@pytest.mark.asyncio
async def test_unauthenticated_research_apis_rejected(db_session: AsyncSession, phase21_fixture):
    """Unauthenticated access to research collection and detail endpoints returns 401."""
    exp_p7 = phase21_fixture["exp_p7"]
    smp_p7 = phase21_fixture["smp_p7"]

    async with make_client(db_session) as ac:
        res1 = await ac.get("/api/v1/experiments")
        assert res1.status_code == 401

        res2 = await ac.get(f"/api/v1/experiments/{exp_p7.id}")
        assert res2.status_code == 401

        res3 = await ac.get("/api/v1/samples")
        assert res3.status_code == 401

        res4 = await ac.get(f"/api/v1/samples/{smp_p7.id}")
        assert res4.status_code == 401

        res5 = await ac.get(f"/api/v1/reports/experiments/{exp_p7.id}/summary")
        assert res5.status_code == 401


# ── TEST 2: ADMIN SYSTEM-WIDE ACCESS (200) ───────────────────────────

@pytest.mark.asyncio
async def test_admin_system_wide_research_access(db_session: AsyncSession, phase21_fixture):
    """Platform Administrator accesses research records across all active projects."""
    token_admin = phase21_fixture["token_admin"]
    exp_p7 = phase21_fixture["exp_p7"]
    exp_p2 = phase21_fixture["exp_p2"]

    async with make_client(db_session, token=token_admin) as ac:
        # Admin gets all experiments
        res = await ac.get("/api/v1/experiments")
        assert res.status_code == 200
        data = res.json()
        codes = [e["experiment_code"] for e in data]
        assert exp_p7.experiment_code in codes
        assert exp_p2.experiment_code in codes

        # Admin accesses individual experiments directly
        res_p7 = await ac.get(f"/api/v1/experiments/{exp_p7.id}")
        assert res_p7.status_code == 200
        assert res_p7.json()["experiment_code"] == exp_p7.experiment_code

        res_p2 = await ac.get(f"/api/v1/experiments/{exp_p2.id}")
        assert res_p2.status_code == 200
        assert res_p2.json()["experiment_code"] == exp_p2.experiment_code


# ── TEST 3: STUDENT PROJECT-SCOPED EXPERIMENTS & SAMPLES (200) ────────

@pytest.mark.asyncio
async def test_student_collection_strictly_project_scoped(db_session: AsyncSession, phase21_fixture):
    """Student A (P7) receives only P7 records; Student B (P2) receives only P2 records."""
    token_a = phase21_fixture["token_a"]
    token_b = phase21_fixture["token_b"]
    exp_p7 = phase21_fixture["exp_p7"]
    exp_p2 = phase21_fixture["exp_p2"]
    smp_p7 = phase21_fixture["smp_p7"]
    smp_p2 = phase21_fixture["smp_p2"]

    # Student A (P7)
    async with make_client(db_session, token=token_a) as ac:
        res_exp_a = await ac.get("/api/v1/experiments")
        assert res_exp_a.status_code == 200
        exp_codes_a = [e["experiment_code"] for e in res_exp_a.json()]
        assert exp_p7.experiment_code in exp_codes_a
        assert exp_p2.experiment_code not in exp_codes_a

        res_smp_a = await ac.get("/api/v1/samples")
        assert res_smp_a.status_code == 200
        smp_codes_a = [s["sample_code"] for s in res_smp_a.json()]
        assert smp_p7.sample_code in smp_codes_a
        assert smp_p2.sample_code not in smp_codes_a

    # Student B (P2)
    async with make_client(db_session, token=token_b) as ac:
        res_exp_b = await ac.get("/api/v1/experiments")
        assert res_exp_b.status_code == 200
        exp_codes_b = [e["experiment_code"] for e in res_exp_b.json()]
        assert exp_p2.experiment_code in exp_codes_b
        assert exp_p7.experiment_code not in exp_codes_b

        res_smp_b = await ac.get("/api/v1/samples")
        assert res_smp_b.status_code == 200
        smp_codes_b = [s["sample_code"] for s in res_smp_b.json()]
        assert smp_p2.sample_code in smp_codes_b
        assert smp_p7.sample_code not in smp_codes_b


# ── TEST 4: CROSS-PROJECT DIRECT ID READ PROTECTION (404/403) ────────

@pytest.mark.asyncio
async def test_cross_project_direct_id_read_denied(db_session: AsyncSession, phase21_fixture):
    """Student A (P7) accessing P2 direct resource UUIDs receives 404/403."""
    token_a = phase21_fixture["token_a"]
    exp_p2 = phase21_fixture["exp_p2"]
    smp_p2 = phase21_fixture["smp_p2"]

    async with make_client(db_session, token=token_a) as ac:
        # Cross-project Experiment
        res1 = await ac.get(f"/api/v1/experiments/{exp_p2.id}")
        assert res1.status_code in (403, 404)

        # Cross-project Sample
        res2 = await ac.get(f"/api/v1/samples/{smp_p2.id}")
        assert res2.status_code in (403, 404)

        # Cross-project Report Summary
        res3 = await ac.get(f"/api/v1/reports/experiments/{exp_p2.id}/summary")
        assert res3.status_code in (403, 404)

        # Cross-project PDF Report
        res4 = await ac.get(f"/api/v1/reports/experiments/{exp_p2.id}/pdf")
        assert res4.status_code in (403, 404)


# ── TEST 5: CROSS-PROJECT WRITE & TAMPER PROTECTION (403/404) ─────────

@pytest.mark.asyncio
async def test_cross_project_write_operations_denied(db_session: AsyncSession, phase21_fixture):
    """Student A (P7) cannot update or delete P2 resources, or create experiments assigned to P2."""
    token_a = phase21_fixture["token_a"]
    p2 = phase21_fixture["p2"]
    exp_p2 = phase21_fixture["exp_p2"]

    async with make_client(db_session, token=token_a) as ac:
        # Cross-project POST attempt
        post_payload = {
            "project_id": str(p2.id),
            "experiment_code": f"EXP-HACK-{uuid.uuid4().hex[:4]}",
            "title": "Unauthorized P2 Injection",
            "status": "PLANNED",
        }
        res_post = await ac.post("/api/v1/experiments", json=post_payload)
        assert res_post.status_code == 403

        # Cross-project PUT update attempt
        put_payload = {
            "title": "Tampered P2 Experiment Title",
            "status": "IN_PROGRESS",
        }
        res_put = await ac.put(f"/api/v1/experiments/{exp_p2.id}", json=put_payload)
        assert res_put.status_code in (403, 404)

        # Cross-project DELETE attempt
        res_del = await ac.delete(f"/api/v1/experiments/{exp_p2.id}")
        assert res_del.status_code in (403, 404)


# ── TEST 6: QUERY PARAMETER TAMPER IMMUNITY (403) ────────────────────

@pytest.mark.asyncio
async def test_query_parameter_tamper_rejected(db_session: AsyncSession, phase21_fixture):
    """Student passing ?project_id={OTHER_PROJECT} receives 403 Forbidden across research domains."""
    token_a = phase21_fixture["token_a"]
    p2 = phase21_fixture["p2"]

    async with make_client(db_session, token=token_a) as ac:
        # Experiments
        res_exp = await ac.get(f"/api/v1/experiments?project_id={p2.id}")
        assert res_exp.status_code == 403

        # Samples
        res_smp = await ac.get(f"/api/v1/samples?project_id={p2.id}")
        assert res_smp.status_code == 403

        # ML Datasets
        res_ml = await ac.get(f"/api/v1/ml/datasets?project_id={p2.id}")
        assert res_ml.status_code == 403

        # DOE Objectives
        res_doe = await ac.get(f"/api/v1/objectives?project_id={p2.id}")
        assert res_doe.status_code == 403

        # Recommendations
        res_rec = await ac.get(f"/api/v1/recommendations?project_id={p2.id}")
        assert res_rec.status_code == 403

        # Optimization Objectives
        res_opt = await ac.get(f"/api/v1/optimization/objectives?project_id={p2.id}")
        assert res_opt.status_code == 403


# ── TEST 7: UNGROUPED STUDENT DENIED RESEARCH ACCESS (403) ───────────

@pytest.mark.asyncio
async def test_ungrouped_student_denied_research_access(db_session: AsyncSession, phase21_fixture):
    """Student C without active group membership receives 403 NO_ACTIVE_GROUP."""
    token_c = phase21_fixture["token_c"]

    async with make_client(db_session, token=token_c) as ac:
        res1 = await ac.get("/api/v1/experiments")
        assert res1.status_code == 403
        assert "NO_ACTIVE_GROUP" in str(res1.json())

        res2 = await ac.get("/api/v1/samples")
        assert res2.status_code == 403
        assert "NO_ACTIVE_GROUP" in str(res2.json())

        res3 = await ac.get("/api/v1/dashboard/stats")
        assert res3.status_code == 403
        assert "NO_ACTIVE_GROUP" in str(res3.json())
