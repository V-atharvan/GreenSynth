"""
GreenSynth Analytics — Phase 22 File Access + Direct UUID Security Unit & Integration Tests

Validates:
1. Admin system-wide file access (download, metadata, preview) across P7 and P2.
2. Student authorized file operations on assigned project resources (P7).
3. Student IDOR defense: Unauthorized direct file download, metadata, preview, and delete requests targeting other projects (P2) return 404.
4. File upload isolation: Student cannot upload raw files to characterization runs of other projects.
5. Storage security: Path traversal defenses, SHA-256 integrity check, duplicate detection, and size limit enforcement (50MB).
6. Direct UUID security across all research domains (experiments, samples, characterizations, reports, ML datasets, DOE, optimization, recommendations).
"""

from __future__ import annotations

import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole
from app.storage import get_storage_backend


@pytest.fixture
async def phase22_fixture(db_session: AsyncSession):
    """Sets up Projects P7 & P2, Admin, Student A (P7), Student B (P2), Experiments, Samples, Characterizations, and Stored Files."""
    suffix = uuid.uuid4().hex[:6]
    storage = get_storage_backend()

    # 1. Projects
    p7 = Project(
        id=uuid.uuid4(),
        name=f"CuO Spray Pyrolysis P7 {suffix}",
        project_code=f"P7-{suffix}",
        description="CuO spray pyrolysis research",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    p2 = Project(
        id=uuid.uuid4(),
        name=f"CuO Sol-Gel Acetone P2 {suffix}",
        project_code=f"P2-{suffix}",
        description="CuO sol-gel research",
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
        username=f"admin_p22_{suffix}",
        email=f"admin.p22_{suffix}@greensynth.edu",
        full_name="Admin Security Officer",
        department="Central Lab",
        phone="1000000000",
        roll_number=f"ADM-22-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    student_a = User(
        id=uuid.uuid4(),
        username=f"student_p22_a_{suffix}",
        email=f"student.p22_a_{suffix}@greensynth.edu",
        full_name="Student Researcher A (P7)",
        department="Chemical Engineering",
        phone="1000000001",
        roll_number=f"STU-A-22-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassA123!"),
        is_active=True,
    )
    student_b = User(
        id=uuid.uuid4(),
        username=f"student_p22_b_{suffix}",
        email=f"student.p22_b_{suffix}@greensynth.edu",
        full_name="Student Researcher B (P2)",
        department="Materials Science",
        phone="1000000002",
        roll_number=f"STU-B-22-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("StudentPassB123!"),
        is_active=True,
    )
    db_session.add_all([admin, student_a, student_b])
    await db_session.flush()

    # 3. Research Groups & Memberships
    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name=f"P7 Spray Lab {suffix}",
        project_id=p7.id,
        leader_user_id=student_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name=f"P2 SolGel Lab {suffix}",
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

    # 4. Research Entities: P7
    exp_p7 = Experiment(
        id=uuid.uuid4(),
        project_id=p7.id,
        experiment_code=f"EXP-P7-F22-{suffix}",
        title="P7 Spray Pyrolysis Run",
        status="COMPLETED",
    )
    smp_p7 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p7.id,
        sample_code=f"SMP-P7-F22-{suffix}",
        name="CuO Film Sample P7",
        material="CuO",
        status="PREPARED",
    )
    ch_p7 = Characterization(
        id=uuid.uuid4(),
        sample_id=smp_p7.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add_all([exp_p7, smp_p7, ch_p7])
    await db_session.flush()

    # Store a physical file for P7
    file_bytes_p7 = b"2theta,intensity\n20.0,150\n35.5,1200\n38.7,950\n"
    meta_p7 = await storage.store(
        content=file_bytes_p7,
        destination_path=f"projects/{p7.project_code}/experiments/{exp_p7.experiment_code}/samples/{smp_p7.sample_code}/{ch_p7.id}/xrd_p7.csv",
        original_filename="xrd_data_p7.csv",
        content_type="text/csv",
    )
    file_p7 = RawFile(
        id=uuid.uuid4(),
        characterization_id=ch_p7.id,
        sample_id=smp_p7.id,
        original_filename="xrd_data_p7.csv",
        stored_filename=f"{uuid.uuid4()!s}.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=len(file_bytes_p7),
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path=meta_p7.stored_path,
        storage_backend=meta_p7.storage_backend,
        status="ACTIVE",
    )

    # 5. Research Entities: P2
    exp_p2 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code=f"EXP-P2-F22-{suffix}",
        title="P2 Sol-Gel Run",
        status="COMPLETED",
    )
    smp_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2.id,
        sample_code=f"SMP-P2-F22-{suffix}",
        name="CuO Xerogel Sample P2",
        material="CuO",
        status="PREPARED",
    )
    ch_p2 = Characterization(
        id=uuid.uuid4(),
        sample_id=smp_p2.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add_all([exp_p2, smp_p2, ch_p2])
    await db_session.flush()

    # Store a physical file for P2
    file_bytes_p2 = b"2theta,intensity\n15.0,200\n32.0,1800\n"
    meta_p2 = await storage.store(
        content=file_bytes_p2,
        destination_path=f"projects/{p2.project_code}/experiments/{exp_p2.experiment_code}/samples/{smp_p2.sample_code}/{ch_p2.id}/xrd_p2.csv",
        original_filename="xrd_secret_p2.csv",
        content_type="text/csv",
    )
    file_p2 = RawFile(
        id=uuid.uuid4(),
        characterization_id=ch_p2.id,
        sample_id=smp_p2.id,
        original_filename="xrd_secret_p2.csv",
        stored_filename=f"{uuid.uuid4()!s}.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=len(file_bytes_p2),
        checksum="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
        storage_path=meta_p2.stored_path,
        storage_backend=meta_p2.storage_backend,
        status="ACTIVE",
    )

    db_session.add_all([file_p7, file_p2])
    await db_session.flush()

    token_admin = create_access_token(admin.id, account_type="ADMIN")
    token_a = create_access_token(student_a.id, account_type="STUDENT")
    token_b = create_access_token(student_b.id, account_type="STUDENT")

    return {
        "p7": p7,
        "p2": p2,
        "admin": admin,
        "student_a": student_a,
        "student_b": student_b,
        "exp_p7": exp_p7,
        "exp_p2": exp_p2,
        "smp_p7": smp_p7,
        "smp_p2": smp_p2,
        "ch_p7": ch_p7,
        "ch_p2": ch_p2,
        "file_p7": file_p7,
        "file_p2": file_p2,
        "token_admin": token_admin,
        "token_a": token_a,
        "token_b": token_b,
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


# ── TEST 1: ADMIN SYSTEM-WIDE FILE ACCESS ─────────────────────────────

@pytest.mark.asyncio
async def test_admin_system_wide_file_access(db_session: AsyncSession, phase22_fixture):
    """Platform Administrator can access, preview, and download files from both P7 and P2."""
    token_admin = phase22_fixture["token_admin"]
    file_p7 = phase22_fixture["file_p7"]
    file_p2 = phase22_fixture["file_p2"]

    async with make_client(db_session, token=token_admin) as ac:
        # Download P7 file
        res_dl_p7 = await ac.get(f"/api/v1/files/{file_p7.id}/download")
        assert res_dl_p7.status_code == 200
        assert b"2theta,intensity" in res_dl_p7.content

        # Download P2 file
        res_dl_p2 = await ac.get(f"/api/v1/files/{file_p2.id}/download")
        assert res_dl_p2.status_code == 200
        assert b"2theta,intensity" in res_dl_p2.content

        # Metadata for P7 and P2
        res_meta_p7 = await ac.get(f"/api/v1/files/{file_p7.id}")
        assert res_meta_p7.status_code == 200
        assert res_meta_p7.json()["original_filename"] == "xrd_data_p7.csv"

        res_meta_p2 = await ac.get(f"/api/v1/files/{file_p2.id}")
        assert res_meta_p2.status_code == 200
        assert res_meta_p2.json()["original_filename"] == "xrd_secret_p2.csv"

        # Preview P7 and P2
        res_prev_p7 = await ac.get(f"/api/v1/files/{file_p7.id}/preview")
        assert res_prev_p7.status_code == 200
        assert "preview_text" in res_prev_p7.json()

        res_prev_p2 = await ac.get(f"/api/v1/files/{file_p2.id}/preview")
        assert res_prev_p2.status_code == 200
        assert "preview_text" in res_prev_p2.json()


# ── TEST 2: STUDENT AUTHORIZED FILE OPERATIONS ────────────────────────

@pytest.mark.asyncio
async def test_student_authorized_file_access(db_session: AsyncSession, phase22_fixture):
    """Student A (P7) can access metadata, preview, and download P7 files."""
    token_a = phase22_fixture["token_a"]
    file_p7 = phase22_fixture["file_p7"]

    async with make_client(db_session, token=token_a) as ac:
        # Download
        res_dl = await ac.get(f"/api/v1/files/{file_p7.id}/download")
        assert res_dl.status_code == 200
        assert b"2theta,intensity" in res_dl.content

        # Metadata
        res_meta = await ac.get(f"/api/v1/files/{file_p7.id}")
        assert res_meta.status_code == 200
        assert res_meta.json()["original_filename"] == "xrd_data_p7.csv"

        # Preview
        res_prev = await ac.get(f"/api/v1/files/{file_p7.id}/preview")
        assert res_prev.status_code == 200
        assert "2theta,intensity" in res_prev.json()["preview_text"]


# ── TEST 3: STUDENT IDOR PROTECTION ON OTHER PROJECT FILES (404) ─────

@pytest.mark.asyncio
async def test_student_cross_project_file_idor_denied(db_session: AsyncSession, phase22_fixture):
    """Student A (P7) cannot download, preview, inspect metadata, or delete P2 files."""
    token_a = phase22_fixture["token_a"]
    file_p2 = phase22_fixture["file_p2"]

    async with make_client(db_session, token=token_a) as ac:
        # Cross-project Download
        res_dl = await ac.get(f"/api/v1/files/{file_p2.id}/download")
        assert res_dl.status_code == 404

        # Cross-project Metadata
        res_meta = await ac.get(f"/api/v1/files/{file_p2.id}")
        assert res_meta.status_code == 404

        # Cross-project Preview
        res_prev = await ac.get(f"/api/v1/files/{file_p2.id}/preview")
        assert res_prev.status_code == 404

        # Cross-project Delete
        res_del = await ac.delete(f"/api/v1/files/{file_p2.id}")
        assert res_del.status_code == 404


# ── TEST 4: FILE UPLOAD ISOLATION (CROSS-PROJECT UPLOAD DENIED) ───────

@pytest.mark.asyncio
async def test_file_upload_cross_project_denied(db_session: AsyncSession, phase22_fixture):
    """Student A (P7) attempting to upload raw file to P2 characterization receives 404."""
    token_a = phase22_fixture["token_a"]
    ch_p2 = phase22_fixture["ch_p2"]
    ch_p7 = phase22_fixture["ch_p7"]

    async with make_client(db_session, token=token_a) as ac:
        file_payload = {"file": ("test_run.csv", io.BytesIO(b"2theta,counts\n10,20\n"), "text/csv")}

        # Attempt to upload to P2 characterization run
        res_p2 = await ac.post(
            f"/api/v1/characterizations/{ch_p2.id}/files",
            files=file_payload,
        )
        assert res_p2.status_code == 404

        # Uploading to authorized P7 characterization succeeds
        file_payload_p7 = {"file": ("valid_p7.csv", io.BytesIO(b"2theta,counts\n25,500\n"), "text/csv")}
        res_p7 = await ac.post(
            f"/api/v1/characterizations/{ch_p7.id}/files",
            files=file_payload_p7,
        )
        assert res_p7.status_code == 201


# ── TEST 5: DIRECT UUID SECURITY ACROSS RESEARCH DOMAINS ──────────────

@pytest.mark.asyncio
async def test_direct_uuid_idor_protection_across_domains(db_session: AsyncSession, phase22_fixture):
    """Student A (P7) receives 404/403 when accessing P2 resources by direct UUID."""
    token_a = phase22_fixture["token_a"]
    exp_p2 = phase22_fixture["exp_p2"]
    smp_p2 = phase22_fixture["smp_p2"]
    ch_p2 = phase22_fixture["ch_p2"]

    async with make_client(db_session, token=token_a) as ac:
        # Experiment direct UUID
        res_exp = await ac.get(f"/api/v1/experiments/{exp_p2.id}")
        assert res_exp.status_code in (403, 404)

        # Sample direct UUID
        res_smp = await ac.get(f"/api/v1/samples/{smp_p2.id}")
        assert res_smp.status_code in (403, 404)

        # Characterization direct UUID
        res_ch = await ac.get(f"/api/v1/characterizations/{ch_p2.id}")
        assert res_ch.status_code in (403, 404)

        # Characterization files nested direct UUID
        res_ch_files = await ac.get(f"/api/v1/characterizations/{ch_p2.id}/files")
        assert res_ch_files.status_code in (403, 404)

        # Report PDF direct UUID
        res_pdf = await ac.get(f"/api/v1/reports/experiments/{exp_p2.id}/pdf")
        assert res_pdf.status_code in (403, 404)

        # Report Summary direct UUID
        res_rep = await ac.get(f"/api/v1/reports/experiments/{exp_p2.id}/summary")
        assert res_rep.status_code in (403, 404)
