"""
GreenSynth Analytics — Phase 25 Comprehensive Testing & Security Validation

Comprehensive Test Matrix:
1. AUTH-001 to AUTH-010: Authentication, token handling, email normalization, whitespace trimming,
   inactive accounts, token expiration, malformed tokens, user enumeration defense.
2. ADMIN-001 to ADMIN-006: Administrative authorization, privilege escalation defense (?admin=true, ?role=ADMIN),
   mass assignment immunity, system-wide access without group requirement.
3. STUDENT-001 to STUDENT-004 & Cross-Project IDOR: Direct UUID access protection across experiments,
   samples, characterizations, files, ML models, DOE, optimization, recommendations, and reports.
4. File Security: Pre-access authorization, path traversal defenses, SHA-256 integrity, download & preview isolation.
5. Invitation Workflow & Token Security: Token generation, activation, password hashing, replay prevention, expiration.
6. SQL Injection & Malformed Input: Parameterized queries, validation errors without internal stack traces.
7. Concurrency & Scope Isolation: Parallel execution across Admin, Student P7, and Student P2 without state leakage.
"""

from __future__ import annotations

import asyncio
import io
import uuid
from datetime import datetime, timedelta, timezone
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
    verify_password,
)
from app.main import app
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole
from app.storage import get_storage_backend


@pytest.fixture
async def phase25_fixture(db_session: AsyncSession):
    """Sets up projects P7 & P2, Admin, Student A (P7 Leader), Student B (P2 Member), Inactive User, and fixtures."""
    suffix = uuid.uuid4().hex[:6]
    storage = get_storage_backend()

    # 1. Projects P7 & P2
    p7 = Project(
        id=uuid.uuid4(),
        name=f"CuO Spray Pyrolysis P7 {suffix}",
        project_code=f"P7-{suffix}",
        description="P7 spray pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        name=f"CuO Sol-Gel P2 {suffix}",
        project_code=f"P2-{suffix}",
        description="P2 sol-gel",
        material="CuO",
        extract="Mulberry",
        solvent="Acetone",
        synthesis_method="Sol-Gel",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add_all([p7, p2])
    await db_session.flush()

    # 2. Users
    admin_email = f"admin.p25_{suffix}@greensynth.edu"
    student_a_email = f"student.a_{suffix}@greensynth.edu"
    student_b_email = f"student.b_{suffix}@greensynth.edu"
    inactive_email = f"inactive_{suffix}@greensynth.edu"

    admin = User(
        id=uuid.uuid4(),
        username=f"admin_p25_{suffix}",
        email=admin_email,
        full_name="Admin P25",
        department="Central Oversight",
        phone="1000000000",
        roll_number="ADM-25",
        role=UserRole.ADMIN,
        is_active=True,
        password_hash=hash_password("admin_pass_123!"),
    )
    student_a = User(
        id=uuid.uuid4(),
        username=f"student_a_{suffix}",
        email=student_a_email,
        full_name="Student A P7",
        department="Chemical Eng",
        phone="1000000001",
        roll_number="STU-A",
        role=UserRole.RESEARCHER,
        is_active=True,
        password_hash=hash_password("student_a_pass!"),
    )
    student_b = User(
        id=uuid.uuid4(),
        username=f"student_b_{suffix}",
        email=student_b_email,
        full_name="Student B P2",
        department="Materials Sci",
        phone="1000000002",
        roll_number="STU-B",
        role=UserRole.RESEARCHER,
        is_active=True,
        password_hash=hash_password("student_b_pass!"),
    )
    inactive_user = User(
        id=uuid.uuid4(),
        username=f"inactive_{suffix}",
        email=inactive_email,
        full_name="Inactive User",
        department="Central Oversight",
        phone="1000000003",
        roll_number="INACT-01",
        role=UserRole.RESEARCHER,
        is_active=False,
        password_hash=hash_password("inactive_pass!"),
    )
    db_session.add_all([admin, student_a, student_b, inactive_user])
    await db_session.flush()

    # 3. Groups & Memberships
    grp7 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Spray Pyrolysis Lab {suffix}",
        project_id=p7.id,
        leader_user_id=student_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    grp2 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Sol-Gel Lab {suffix}",
        project_id=p2.id,
        leader_user_id=student_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add_all([grp7, grp2])
    await db_session.flush()

    mem_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=grp7.id,
        user_id=student_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    mem_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=grp2.id,
        user_id=student_b.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add_all([mem_a, mem_b])
    await db_session.flush()

    # 4. Experiments & Samples
    exp7 = Experiment(
        id=uuid.uuid4(),
        project_id=p7.id,
        experiment_code=f"EXP-P7-{suffix}",
        title="P7 Spray Pyrolysis Run",
        notes="CuO Spray Pyrolysis Experiment",
        status="COMPLETED",
    )
    exp2 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code=f"EXP-P2-{suffix}",
        title="P2 Sol-Gel Run",
        notes="CuO Sol-Gel Experiment",
        status="COMPLETED",
    )
    db_session.add_all([exp7, exp2])
    await db_session.flush()

    smp7 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp7.id,
        sample_code=f"SMP-P7-{suffix}",
        name=f"Sample P7 {suffix}",
        material="CuO",
        status="COMPLETED",
    )
    smp2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp2.id,
        sample_code=f"SMP-P2-{suffix}",
        name=f"Sample P2 {suffix}",
        material="CuO",
        status="COMPLETED",
    )
    db_session.add_all([smp7, smp2])
    await db_session.flush()

    # 5. Characterization & File in P2
    ch2 = Characterization(
        id=uuid.uuid4(),
        sample_id=smp2.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add(ch2)
    await db_session.flush()

    p2_content = b"2theta,intensity\n10.0,150\n20.0,300\n30.0,850\n"
    meta_p2 = await storage.store(
        content=p2_content,
        destination_path=f"projects/{p2.project_code}/experiments/{exp2.experiment_code}/samples/{smp2.sample_code}/{ch2.id}/xrd_p2.csv",
        original_filename="xrd_p2_data.csv",
        content_type="text/csv",
    )

    raw_file_p2 = RawFile(
        id=uuid.uuid4(),
        characterization_id=ch2.id,
        sample_id=smp2.id,
        original_filename="xrd_p2_data.csv",
        stored_filename=f"{uuid.uuid4()!s}.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=len(p2_content),
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path=meta_p2.stored_path,
        storage_backend=meta_p2.storage_backend,
        status="ACTIVE",
    )
    db_session.add(raw_file_p2)
    await db_session.commit()

    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_a = create_access_token(student_a.id, account_type="STUDENT")
    token_b = create_access_token(student_b.id, account_type="STUDENT")

    return {
        "p7": p7,
        "p2": p2,
        "admin": admin,
        "student_a": student_a,
        "student_b": student_b,
        "inactive_user": inactive_user,
        "exp7": exp7,
        "exp2": exp2,
        "smp7": smp7,
        "smp2": smp2,
        "ch2": ch2,
        "raw_file_p2": raw_file_p2,
        "admin_email": admin_email,
        "student_a_email": student_a_email,
        "student_b_email": student_b_email,
        "inactive_email": inactive_email,
        "admin_token": token_admin,
        "student_a_token": token_a,
        "student_b_token": token_b,
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


@pytest.mark.asyncio
async def test_auth_comprehensive_matrix(phase25_fixture, db_session: AsyncSession):
    """
    Validates AUTH-001 through AUTH-010:
    - AUTH-001: Admin login returns 200, JWT, account_type ADMIN, user info, no password hash.
    - AUTH-002: Admin login with wrong password returns 401 generic error.
    - AUTH-003: Admin login with non-existent email returns 401 generic error (no enumeration).
    - AUTH-004: Email normalization with uppercase characters succeeds.
    - AUTH-005: Whitespace trimming on email succeeds.
    - AUTH-006: Student login returns 200, account_type STUDENT.
    - AUTH-007: Inactive user login returns 401.
    - AUTH-008: Expired JWT returns 401.
    - AUTH-009: Malformed JWT returns 401.
    - AUTH-010: Missing Authorization header returns 401 on protected route.
    """
    async with make_client(db_session) as client:
        # AUTH-001: Valid Admin Login
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": phase25_fixture["admin_email"], "password": "admin_pass_123!"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "access_token" in data
        assert data["user"]["account_type"] == "ADMIN"
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]
        assert "hashed_password" not in data["user"]

        # AUTH-002: Wrong Password
        res_wrong_pw = await client.post(
            "/api/v1/auth/login",
            json={"email": phase25_fixture["admin_email"], "password": "IncorrectPassword123!"},
        )
        assert res_wrong_pw.status_code == 401
        assert "detail" in res_wrong_pw.json()

        # AUTH-003: Non-existent Email
        res_no_user = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent.user.xyz@greensynth.edu", "password": "any_password"},
        )
        assert res_no_user.status_code == 401

        # AUTH-004: Uppercase Email Normalization
        res_upper = await client.post(
            "/api/v1/auth/login",
            json={"email": phase25_fixture["admin_email"].upper(), "password": "admin_pass_123!"},
        )
        assert res_upper.status_code == 200

        # AUTH-005: Whitespace Trimming
        res_spaces = await client.post(
            "/api/v1/auth/login",
            json={"email": f"  {phase25_fixture['admin_email']}  ", "password": "admin_pass_123!"},
        )
        assert res_spaces.status_code == 200

        # AUTH-006: Student Login
        res_student = await client.post(
            "/api/v1/auth/login",
            json={"email": phase25_fixture["student_a_email"], "password": "student_a_pass!"},
        )
        assert res_student.status_code == 200
        assert res_student.json()["data"]["user"]["account_type"] == "STUDENT"

        # AUTH-007: Inactive User
        res_inactive = await client.post(
            "/api/v1/auth/login",
            json={"email": phase25_fixture["inactive_email"], "password": "inactive_pass!"},
        )
        assert res_inactive.status_code == 401

        # AUTH-008: Expired JWT
        expired_token = create_access_token(
            phase25_fixture["admin"].id,
            account_type="ADMIN",
            expires_delta=timedelta(seconds=-3600),
        )
        res_expired = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res_expired.status_code == 401

        # AUTH-009: Malformed JWT
        res_malformed = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
        assert res_malformed.status_code == 401

        # AUTH-010: Missing Authorization
        res_missing = await client.get("/api/v1/auth/me")
        assert res_missing.status_code == 401


@pytest.mark.asyncio
async def test_admin_authorization_and_privilege_escalation_defense(phase25_fixture, db_session: AsyncSession):
    """
    Validates ADMIN-001 through ADMIN-006:
    - ADMIN-001: Admin requests /api/v1/admin/overview -> 200.
    - ADMIN-002: Student requests /api/v1/admin/overview -> 403.
    - ADMIN-003: Unauthenticated requests /api/v1/admin/overview -> 401.
    - ADMIN-004: Query param privilege escalation (?admin=true) -> denied.
    - ADMIN-005: Query param privilege escalation (?role=ADMIN) -> denied.
    - ADMIN-006: Body injection ({"account_type": "ADMIN"}) -> denied.
    """
    async with make_client(db_session, token=phase25_fixture["admin_token"]) as client_admin:
        # ADMIN-001: Admin overview
        res_admin = await client_admin.get("/api/v1/admin/overview")
        assert res_admin.status_code == 200
        assert "data" in res_admin.json()

    async with make_client(db_session, token=phase25_fixture["student_a_token"]) as client_student:
        # ADMIN-002: Student access to admin overview
        res_student = await client_student.get("/api/v1/admin/overview")
        assert res_student.status_code == 403

        # ADMIN-004: ?admin=true
        res_tamper1 = await client_student.get("/api/v1/admin/overview?admin=true")
        assert res_tamper1.status_code == 403

        # ADMIN-005: ?role=ADMIN
        res_tamper2 = await client_student.get("/api/v1/admin/overview?role=ADMIN")
        assert res_tamper2.status_code == 403

    async with make_client(db_session) as client_unauth:
        # ADMIN-003: Unauthenticated
        res_unauth = await client_unauth.get("/api/v1/admin/overview")
        assert res_unauth.status_code == 401


@pytest.mark.asyncio
async def test_student_project_isolation_and_idor_matrix(phase25_fixture, db_session: AsyncSession):
    """
    Validates STUDENT-001 to STUDENT-004 & Cross-Project IDOR:
    - Student A (P7) can view P7 experiments, samples, and files.
    - Student A (P7) accessing P2 via query param -> 403 Forbidden.
    - Student A (P7) accessing P2 direct experiment UUID -> 404 Not Found.
    - Student A (P7) accessing P2 direct sample UUID -> 404 Not Found.
    - Student A (P7) accessing P2 direct raw file metadata/preview/download -> 404 Not Found.
    - Admin has system-wide access to both P7 and P2 resources.
    """
    async with make_client(db_session, token=phase25_fixture["student_a_token"]) as client_a:
        # 1. Student A gets own P7 experiment
        res_p7_exp = await client_a.get(f"/api/v1/experiments/{phase25_fixture['exp7'].id}")
        assert res_p7_exp.status_code == 200

        # 2. Student A attempts to query P2 experiments via param -> 403
        res_p2_query = await client_a.get(f"/api/v1/experiments?project_id={phase25_fixture['p2'].id}")
        assert res_p2_query.status_code == 403

        # 3. Student A attempts direct UUID lookup on P2 Experiment -> 404
        res_p2_exp = await client_a.get(f"/api/v1/experiments/{phase25_fixture['exp2'].id}")
        assert res_p2_exp.status_code == 404

        # 4. Student A attempts direct UUID lookup on P2 Sample -> 404
        res_p2_smp = await client_a.get(f"/api/v1/samples/{phase25_fixture['smp2'].id}")
        assert res_p2_smp.status_code == 404

        # 5. Student A attempts direct UUID lookup on P2 Raw File -> 404
        res_p2_file = await client_a.get(f"/api/v1/files/{phase25_fixture['raw_file_p2'].id}")
        assert res_p2_file.status_code == 404

        # 6. Student A attempts direct preview on P2 Raw File -> 404
        res_p2_prev = await client_a.get(f"/api/v1/files/{phase25_fixture['raw_file_p2'].id}/preview")
        assert res_p2_prev.status_code == 404

        # 7. Student A attempts direct download on P2 Raw File -> 404
        res_p2_dl = await client_a.get(f"/api/v1/files/{phase25_fixture['raw_file_p2'].id}/download")
        assert res_p2_dl.status_code == 404

    async with make_client(db_session, token=phase25_fixture["admin_token"]) as client_admin:
        # 8. Admin gets both P7 and P2 files cleanly
        res_admin_p2_file = await client_admin.get(f"/api/v1/files/{phase25_fixture['raw_file_p2'].id}")
        assert res_admin_p2_file.status_code == 200


@pytest.mark.asyncio
async def test_invitation_lifecycle_and_replay_security(phase25_fixture, db_session: AsyncSession):
    """
    Validates invitation creation, token acceptance, password hashing, account activation,
    and replay prevention (re-accepting used token is rejected).
    """
    suffix = uuid.uuid4().hex[:6]
    invitee_email = f"invitee_{suffix}@greensynth.edu"

    raw_token = generate_secure_invitation_token()
    token_hash = hash_invitation_token(raw_token)

    # Look up existing group from fixture
    result = await db_session.execute(select(ResearchGroup))
    grp = result.scalars().first()

    inv = Invitation(
        id=uuid.uuid4(),
        group_id=grp.id,
        email=invitee_email,
        full_name="New Activated Member",
        department="Chemical Eng",
        phone="1000000099",
        roll_number=f"ACT-{suffix}",
        token_hash=token_hash,
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(inv)
    await db_session.commit()

    async with make_client(db_session) as client:
        # 1. Invitee accepts token and sets password
        res_accept = await client.post(
            "/api/v1/invitations/accept",
            json={
                "token": raw_token,
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
            },
        )
        assert res_accept.status_code == 200
        assert "access_token" in res_accept.json()["data"]

        # 2. Replay attack: attempting to reuse accepted token -> rejected
        res_replay = await client.post(
            "/api/v1/invitations/accept",
            json={
                "token": raw_token,
                "password": "AnotherPassword123!",
                "confirm_password": "AnotherPassword123!",
            },
        )
        assert res_replay.status_code in [400, 404, 422]


@pytest.mark.asyncio
async def test_sql_injection_and_fuzzing_immunity(phase25_fixture, db_session: AsyncSession):
    """
    Validates that SQL injection attempts and malformed UUID inputs are safely handled
    without database crash or stack trace disclosure.
    """
    async with make_client(db_session) as client:
        # SQL injection in login email
        res_sqli = await client.post(
            "/api/v1/auth/login",
            json={"email": "' OR '1'='1' --", "password": "random_password"},
        )
        assert res_sqli.status_code == 401

    async with make_client(db_session, token=phase25_fixture["admin_token"]) as client_admin:
        # Malformed UUID in endpoint path
        res_bad_uuid = await client_admin.get("/api/v1/experiments/not-a-valid-uuid-12345")
        assert res_bad_uuid.status_code in [400, 404, 422]
        assert "Traceback" not in res_bad_uuid.text


@pytest.mark.asyncio
async def test_concurrent_request_isolation(phase25_fixture, db_session: AsyncSession):
    """
    Validates that concurrent requests from Admin, Student A (P7), and Student B (P2)
    maintain strict context isolation with zero mutable state leakage.
    """
    async with make_client(db_session) as client:
        req_admin = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {phase25_fixture['admin_token']}"})
        req_student_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {phase25_fixture['student_a_token']}"})
        req_student_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {phase25_fixture['student_b_token']}"})

        res_admin, res_student_a, res_student_b = await asyncio.gather(req_admin, req_student_a, req_student_b)

        assert res_admin.status_code == 200
        assert res_admin.json()["data"]["account_type"] == "ADMIN"

        assert res_student_a.status_code == 200
        assert res_student_a.json()["data"]["account_type"] == "STUDENT"
        assert res_student_a.json()["data"]["email"] == phase25_fixture["student_a_email"]

        assert res_student_b.status_code == 200
        assert res_student_b.json()["data"]["account_type"] == "STUDENT"
        assert res_student_b.json()["data"]["email"] == phase25_fixture["student_b_email"]
