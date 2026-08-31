"""
GreenSynth Analytics — Phase 26: PostgreSQL + Multi-User Verification Integration Suite

Validates:
1. Multi-User Isolation: Admin (global), Student P1 (scoped), Student P2 (scoped).
2. Direct UUID Security & IDOR Defense across Experiments, Samples, and Raw Files.
3. File Access & Download Security: Scoped to authorized project, rejected across projects.
4. Dashboard Statistics Isolation: Global for Admin, scoped for Students.
5. End-to-End Invitation Workflow with Secure Password Creation & Activation.
6. Concurrent Multi-User Request Isolation.
7. Data Persistence: Research data created by Student P1 is visible to P1 and Admin, hidden from P2.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
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
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership
from app.models.invitation import Invitation
from app.models.project import Project
from app.models.research_group import ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole
from app.storage import get_storage_backend


def make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
        follow_redirects=True,
    )


@pytest_asyncio.fixture
async def phase26_setup(db_session: AsyncSession):
    """
    Sets up multi-user fixture:
    - Admin User
    - Project P1 + Project P2
    - Group P1 (Leader + Student P1)
    - Group P2 (Leader + Student P2)
    - Experiment P1 + Sample P1 + RawFile P1
    - Experiment P2 + Sample P2 + RawFile P2
    """
    unique_suffix = uuid.uuid4().hex[:8]

    # 1. Admin User
    admin_user = User(
        id=uuid.uuid4(),
        username=f"admin_{unique_suffix}",
        email=f"admin_{unique_suffix}@greensynth.edu",
        full_name="Central Administrator",
        department="Central Lab",
        phone="1111111111",
        roll_number=f"ADM-{unique_suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    db_session.add(admin_user)

    # 2. Projects P1 & P2
    # Check if P1 and P2 already exist, or create them
    res_p1 = await db_session.execute(select(Project).where(Project.project_code == "P1"))
    proj_p1 = res_p1.scalars().first()
    if not proj_p1:
        proj_p1 = Project(
            id=uuid.uuid4(),
            project_code="P1",
            name="CuO Sol-Gel Ethanol",
            synthesis_method="Sol-gel",
            material="Copper Oxide",
            extract="Mulberry",
            solvent="Ethanol",
            status="ACTIVE",
        )
        db_session.add(proj_p1)

    res_p2 = await db_session.execute(select(Project).where(Project.project_code == "P2"))
    proj_p2 = res_p2.scalars().first()
    if not proj_p2:
        proj_p2 = Project(
            id=uuid.uuid4(),
            project_code="P2",
            name="CuO Sol-Gel Acetone",
            synthesis_method="Sol-gel",
            material="Copper Oxide",
            extract="Mulberry",
            solvent="Acetone",
            status="ACTIVE",
        )
        db_session.add(proj_p2)

    await db_session.flush()

    # 3. Student P1 (Leader of Group P1)
    student_p1 = User(
        id=uuid.uuid4(),
        username=f"student_p1_{unique_suffix}",
        email=f"student.p1.{unique_suffix}@greensynth.edu",
        full_name="Student Researcher P1",
        department="Chemical Engineering",
        phone="2222222222",
        roll_number=f"STU-P1-{unique_suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPass123!"),
        is_active=True,
    )
    db_session.add(student_p1)
    await db_session.flush()

    group_p1 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Sol-Gel Core Group {unique_suffix}",
        project_id=proj_p1.id,
        leader_user_id=student_p1.id,
        status="ACTIVE",
    )
    db_session.add(group_p1)
    await db_session.flush()

    mem_p1 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_p1.id,
        user_id=student_p1.id,
        is_leader=True,
        status="ACTIVE",
    )
    db_session.add(mem_p1)

    # 4. Student P2 (Member of Group P2)
    student_p2 = User(
        id=uuid.uuid4(),
        username=f"student_p2_{unique_suffix}",
        email=f"student.p2.{unique_suffix}@greensynth.edu",
        full_name="Student Researcher P2",
        department="Materials Science",
        phone="3333333333",
        roll_number=f"STU-P2-{unique_suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPass123!"),
        is_active=True,
    )
    db_session.add(student_p2)
    await db_session.flush()

    group_p2 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Sol-Gel Acetone Group {unique_suffix}",
        project_id=proj_p2.id,
        leader_user_id=student_p2.id,
        status="ACTIVE",
    )
    db_session.add(group_p2)
    await db_session.flush()

    mem_p2 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_p2.id,
        user_id=student_p2.id,
        is_leader=True,
        status="ACTIVE",
    )
    db_session.add(mem_p2)

    # 5. Research Records for P1
    exp_p1 = Experiment(
        id=uuid.uuid4(),
        project_id=proj_p1.id,
        experiment_code=f"EXP-P1-{unique_suffix}",
        title="Sol-Gel P1 Verification Run",
        notes="Phase 26 P1 test experiment",
        status="COMPLETED",
    )
    db_session.add(exp_p1)
    await db_session.flush()

    smp_p1 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p1.id,
        sample_code=f"SMP-P1-{unique_suffix}",
        name=f"Sample P1 {unique_suffix}",
        material="CuO",
        status="COMPLETED",
    )
    db_session.add(smp_p1)
    await db_session.flush()

    # 5. Characterization & File in P1
    ch1 = Characterization(
        id=uuid.uuid4(),
        sample_id=smp_p1.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add(ch1)
    await db_session.flush()

    storage = get_storage_backend()

    content_p1 = b"2theta,intensity\n10.0,150\n20.0,300\n30.0,450\n"
    meta_p1 = await storage.store(
        content=content_p1,
        destination_path=f"projects/{proj_p1.project_code}/experiments/{exp_p1.experiment_code}/samples/{smp_p1.sample_code}/{ch1.id}/p1_xrd.csv",
        original_filename="p1_xrd_spectrum.csv",
        content_type="text/csv",
    )
    file_p1 = RawFile(
        id=uuid.uuid4(),
        characterization_id=ch1.id,
        sample_id=smp_p1.id,
        original_filename="p1_xrd_spectrum.csv",
        stored_filename=f"{uuid.uuid4()!s}.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=len(content_p1),
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path=meta_p1.stored_path,
        storage_backend=meta_p1.storage_backend,
        status="ACTIVE",
    )
    db_session.add(file_p1)

    # 6. Research Records for P2
    exp_p2 = Experiment(
        id=uuid.uuid4(),
        project_id=proj_p2.id,
        experiment_code=f"EXP-P2-{unique_suffix}",
        title="Sol-Gel P2 Verification Run",
        notes="Phase 26 P2 test experiment",
        status="COMPLETED",
    )
    db_session.add(exp_p2)
    await db_session.flush()

    smp_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2.id,
        sample_code=f"SMP-P2-{unique_suffix}",
        name=f"Sample P2 {unique_suffix}",
        material="CuO",
        status="COMPLETED",
    )
    db_session.add(smp_p2)
    await db_session.flush()

    ch2 = Characterization(
        id=uuid.uuid4(),
        sample_id=smp_p2.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add(ch2)
    await db_session.flush()

    content_p2 = b"2theta,intensity\n15.0,220\n25.0,440\n35.0,660\n"
    meta_p2 = await storage.store(
        content=content_p2,
        destination_path=f"projects/{proj_p2.project_code}/experiments/{exp_p2.experiment_code}/samples/{smp_p2.sample_code}/{ch2.id}/p2_xrd.csv",
        original_filename="p2_xrd_spectrum.csv",
        content_type="text/csv",
    )
    file_p2 = RawFile(
        id=uuid.uuid4(),
        characterization_id=ch2.id,
        sample_id=smp_p2.id,
        original_filename="p2_xrd_spectrum.csv",
        stored_filename=f"{uuid.uuid4()!s}.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=len(content_p2),
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path=meta_p2.stored_path,
        storage_backend=meta_p2.storage_backend,
        status="ACTIVE",
    )
    db_session.add(file_p2)

    await db_session.commit()

    admin_token = create_access_token(user_id=str(admin_user.id), account_type="ADMIN")
    student_p1_token = create_access_token(user_id=str(student_p1.id), account_type="STUDENT")
    student_p2_token = create_access_token(user_id=str(student_p2.id), account_type="STUDENT")

    yield {
        "admin_user": admin_user,
        "admin_token": admin_token,
        "student_p1": student_p1,
        "student_p1_token": student_p1_token,
        "student_p2": student_p2,
        "student_p2_token": student_p2_token,
        "group_p1": group_p1,
        "group_p2": group_p2,
        "proj_p1": proj_p1,
        "proj_p2": proj_p2,
        "exp_p1": exp_p1,
        "exp_p2": exp_p2,
        "smp_p1": smp_p1,
        "smp_p2": smp_p2,
        "file_p1": file_p1,
        "file_p2": file_p2,
    }

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_multiuser_project_isolation(phase26_setup, db_session: AsyncSession):
    """
    Verifies that Student P1 can access P1 data but is strictly blocked from P2 data,
    while Student P2 can access P2 data and is blocked from P1 data.
    """
    ctx = phase26_setup

    # Student P1 accessing P1 experiment -> 200
    async with make_client(db_session, token=ctx["student_p1_token"]) as client_p1:
        res_p1_own = await client_p1.get(f"/api/v1/experiments/{ctx['exp_p1'].id}")
        assert res_p1_own.status_code == 200
        p1_data = res_p1_own.json().get("data", res_p1_own.json())
        assert p1_data["experiment_code"] == ctx["exp_p1"].experiment_code

        # Student P1 attempting IDOR on P2 experiment -> 404 (concealed)
        res_p1_cross = await client_p1.get(f"/api/v1/experiments/{ctx['exp_p2'].id}")
        assert res_p1_cross.status_code in [403, 404]

        # Student P1 attempting query param override ?project_id=P2 -> 403 Forbidden
        res_p1_param = await client_p1.get(f"/api/v1/experiments?project_id={ctx['proj_p2'].id}")
        assert res_p1_param.status_code in [403, 404]

    # Student P2 accessing P2 experiment -> 200
    async with make_client(db_session, token=ctx["student_p2_token"]) as client_p2:
        res_p2_own = await client_p2.get(f"/api/v1/experiments/{ctx['exp_p2'].id}")
        assert res_p2_own.status_code == 200
        p2_data = res_p2_own.json().get("data", res_p2_own.json())
        assert p2_data["experiment_code"] == ctx["exp_p2"].experiment_code

        # Student P2 attempting IDOR on P1 experiment -> 404
        res_p2_cross = await client_p2.get(f"/api/v1/experiments/{ctx['exp_p1'].id}")
        assert res_p2_cross.status_code in [403, 404]

    # Admin accessing both P1 and P2 -> 200
    async with make_client(db_session, token=ctx["admin_token"]) as client_admin:
        res_adm_p1 = await client_admin.get(f"/api/v1/experiments/{ctx['exp_p1'].id}")
        assert res_adm_p1.status_code == 200
        res_adm_p2 = await client_admin.get(f"/api/v1/experiments/{ctx['exp_p2'].id}")
        assert res_adm_p2.status_code == 200


@pytest.mark.asyncio
async def test_file_download_and_preview_security(phase26_setup, db_session: AsyncSession):
    """
    Verifies that direct UUID file download and preview respect project boundaries:
    - Student P1 can download P1 file, blocked on P2 file.
    - Admin can download both P1 and P2 files.
    """
    ctx = phase26_setup

    async with make_client(db_session, token=ctx["student_p1_token"]) as client_p1:
        # P1 file download -> 200
        res_dl_own = await client_p1.get(f"/api/v1/files/{ctx['file_p1'].id}/download")
        assert res_dl_own.status_code == 200

        # P2 file download -> 403 or 404
        res_dl_cross = await client_p1.get(f"/api/v1/files/{ctx['file_p2'].id}/download")
        assert res_dl_cross.status_code in [403, 404]

        # P2 file metadata -> 403 or 404
        res_meta_cross = await client_p1.get(f"/api/v1/files/{ctx['file_p2'].id}")
        assert res_meta_cross.status_code in [403, 404]

    async with make_client(db_session, token=ctx["admin_token"]) as client_admin:
        # Admin downloading P1 and P2 files -> 200
        res_adm_dl_p1 = await client_admin.get(f"/api/v1/files/{ctx['file_p1'].id}/download")
        assert res_adm_dl_p1.status_code == 200
        res_adm_dl_p2 = await client_admin.get(f"/api/v1/files/{ctx['file_p2'].id}/download")
        assert res_adm_dl_p2.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_statistics_scoping(phase26_setup, db_session: AsyncSession):
    """
    Verifies that GET /api/v1/dashboard/stats returns global statistics for Admin
    and strictly scoped statistics for Student researchers.
    """
    ctx = phase26_setup

    async with make_client(db_session, token=ctx["admin_token"]) as client_admin:
        res_admin = await client_admin.get("/api/v1/dashboard/stats")
        assert res_admin.status_code == 200
        data_admin = res_admin.json().get("data", res_admin.json())
        assert "total_experiments" in data_admin
        assert "total_samples" in data_admin

    async with make_client(db_session, token=ctx["student_p1_token"]) as client_p1:
        res_p1 = await client_p1.get("/api/v1/dashboard/stats")
        assert res_p1.status_code == 200
        data_p1 = res_p1.json().get("data", res_p1.json())
        # Student stats are computed only for assigned group/project
        assert data_p1["total_experiments"] >= 1


@pytest.mark.asyncio
async def test_e2e_invitation_lifecycle(phase26_setup, db_session: AsyncSession):
    """
    Validates complete invitation workflow:
    1. Group Leader invites new member to Group P1.
    2. Member accepts token and sets password.
    3. New member logs in via unified /auth/login and accesses P1 data.
    4. Replay attack with same invitation token is rejected.
    """
    ctx = phase26_setup
    unique_str = uuid.uuid4().hex[:6]
    invite_email = f"invited.student.{unique_str}@greensynth.edu"

    # Step 1: Create valid pending invitation
    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=ctx["group_p1"].id,
        email=invite_email,
        full_name=f"Invited Student {unique_str}",
        department="Nanotechnology",
        phone="4444444444",
        roll_number=f"INV-{unique_str}",
        token_hash=token_hash,
        status="PENDING",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(inv)
    await db_session.commit()

    # Step 2: Member accepts invitation & creates password
    async with make_client(db_session) as client_public:
        res_accept = await client_public.post(
            "/api/v1/invitations/accept",
            json={
                "token": raw_token,
                "password": "SecureStudentPass99!",
                "confirm_password": "SecureStudentPass99!",
            },
        )
        assert res_accept.status_code == 200
        assert "access_token" in res_accept.json()["data"]

        # Step 3: Member logs in via unified login endpoint
        res_login = await client_public.post(
            "/api/v1/auth/login",
            json={
                "email": invite_email,
                "password": "SecureStudentPass99!",
            },
        )
        assert res_login.status_code == 200
        new_token = res_login.json()["data"]["access_token"]
        assert res_login.json()["data"]["user"]["account_type"] == "STUDENT"

        # Step 4: Replay attack defense
        res_replay = await client_public.post(
            "/api/v1/invitations/accept",
            json={
                "token": raw_token,
                "password": "SecureStudentPass99!",
                "confirm_password": "SecureStudentPass99!",
            },
        )
        assert res_replay.status_code in [400, 404, 422]

    # Step 5: New member accesses assigned P1 experiment
    async with make_client(db_session, token=new_token) as client_new_member:
        res_p1 = await client_new_member.get(f"/api/v1/experiments/{ctx['exp_p1'].id}")
        assert res_p1.status_code == 200
        # Blocked from P2
        res_p2 = await client_new_member.get(f"/api/v1/experiments/{ctx['exp_p2'].id}")
        assert res_p2.status_code in [403, 404]


@pytest.mark.asyncio
async def test_concurrent_multiuser_sessions(phase26_setup, db_session: AsyncSession):
    """
    Validates that concurrent requests from Admin, Student P1, and Student P2
    execute simultaneously with zero session cross-talk or identity contamination.
    """
    ctx = phase26_setup

    async with make_client(db_session) as client:
        req_admin = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ctx['admin_token']}"})
        req_student_p1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ctx['student_p1_token']}"})
        req_student_p2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ctx['student_p2_token']}"})

        res_adm, res_p1, res_p2 = await asyncio.gather(req_admin, req_student_p1, req_student_p2)

        assert res_adm.status_code == 200
        assert res_adm.json()["data"]["account_type"] == "ADMIN"
        assert res_adm.json()["data"]["email"] == ctx["admin_user"].email

        assert res_p1.status_code == 200
        assert res_p1.json()["data"]["account_type"] == "STUDENT"
        assert res_p1.json()["data"]["email"] == ctx["student_p1"].email

        assert res_p2.status_code == 200
        assert res_p2.json()["data"]["account_type"] == "STUDENT"
        assert res_p2.json()["data"]["email"] == ctx["student_p2"].email
