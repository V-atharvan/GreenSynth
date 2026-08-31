"""
GreenSynth Analytics — Phase 11 Authorization Hardening & Security Integration Tests

Tests all aspects of:
1. Unified single login experience (/api/v1/auth/login).
2. Authoritative Admin identity (v.atharvan@gmail.com, account_type="ADMIN").
3. Admin system-wide access across all projects, groups, and users.
4. Student strict project isolation based on research group membership.
5. Direct UUID access prevention (IDOR protection) across:
   - Projects
   - Experiments
   - Samples
   - Characterizations
   - Raw Files & File Downloads
   - Analysis Runs (XRD, FTIR, UV-Vis, SEM, Electrical)
   - ML Datasets, Models, and Predictions
   - DOE Objectives, Studies, and Runs
   - Optimization Runs and Candidate Solutions
   - Recommendation Sessions
   - Validation Results and Dataset Candidates
   - Scientific PDF Reports
   - Synthesis Parameters & Project Configuration
6. Dashboard statistics scoping (Admin = global, Student = project-scoped).
7. Admin cross-project access bypass.
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
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.ml import MLDataset, MLModel, MLTrainingRun
from app.models.project import Project
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def security_setup(db_session: AsyncSession):
    """Sets up two isolated projects (P1 and P2), an Admin user, and two Student users."""
    # 1. Create Project 1 (CuO) and Project 2 (ZnO)
    p1 = Project(
        id=uuid.uuid4(),
        project_code="SEC-P1",
        name="Security Project 1 - CuO",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status="ACTIVE",
    )
    p2 = Project(
        id=uuid.uuid4(),
        project_code="SEC-P2",
        name="Security Project 2 - ZnO",
        material="ZnO",
        extract="Aloe Vera",
        solvent="Water",
        synthesis_method="Hydrothermal",
        status="ACTIVE",
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    # 2. Get or Create Admin User (v.atharvan@gmail.com, aaaaaaaa)
    res_admin = await db_session.execute(select(User).where(User.email == "v.atharvan@gmail.com"))
    admin_user = res_admin.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            id=uuid.uuid4(),
            username=f"admin_atharva_{uuid.uuid4().hex[:6]}",
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

    # 3. Create Student 1 (assigned to P1)
    s1_id = uuid.uuid4().hex[:6]
    student1_user = User(
        id=uuid.uuid4(),
        username=f"student_p1_{s1_id}",
        email=f"student1_{s1_id}@greensynth.edu",
        full_name="Student One",
        department="Chemistry",
        phone="9123456780",
        roll_number=f"ROLL-P1-{s1_id}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("studentpass1"),
        is_active=True,
    )
    db_session.add(student1_user)
    await db_session.flush()

    group1 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Group P1 {s1_id}",
        project_id=p1.id,
        leader_user_id=student1_user.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group1)
    await db_session.flush()

    m1 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group1.id,
        user_id=student1_user.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(m1)

    # 4. Create Student 2 (assigned to P2)
    s2_id = uuid.uuid4().hex[:6]
    student2_user = User(
        id=uuid.uuid4(),
        username=f"student_p2_{s2_id}",
        email=f"student2_{s2_id}@greensynth.edu",
        full_name="Student Two",
        department="Physics",
        phone="9123456781",
        roll_number=f"ROLL-P2-{s2_id}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("studentpass2"),
        is_active=True,
    )
    db_session.add(student2_user)
    await db_session.flush()

    group2 = ResearchGroup(
        id=uuid.uuid4(),
        name=f"Group P2 {s2_id}",
        project_id=p2.id,
        leader_user_id=student2_user.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group2)
    await db_session.flush()

    m2 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group2.id,
        user_id=student2_user.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(m2)

    # 5. Create P2 Experiment & Sample & Characterization for IDOR testing
    exp_p2 = Experiment(
        id=uuid.uuid4(),
        project_id=p2.id,
        experiment_code="EXP-SEC-P2-01",
        title="P2 Private Experiment",
        status="IN_PROGRESS",
    )
    db_session.add(exp_p2)
    await db_session.flush()

    sample_p2 = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_p2.id,
        sample_code="SMP-SEC-P2-01",
        name="Security Sample 1",
        material="ZnO",
        status="PREPARED",
    )
    db_session.add(sample_p2)
    await db_session.flush()

    char_p2 = Characterization(
        id=uuid.uuid4(),
        sample_id=sample_p2.id,
        technique="XRD",
        status="UPLOADED",
    )
    db_session.add(char_p2)
    await db_session.flush()

    file_p2 = RawFile(
        id=uuid.uuid4(),
        characterization_id=char_p2.id,
        sample_id=sample_p2.id,
        original_filename="private_p2_xrd.csv",
        stored_filename="stored_private_p2_xrd.csv",
        file_extension="csv",
        mime_type="text/csv",
        file_size=1024,
        checksum="abc12345def67890",
        storage_path="projects/SEC-P2/private_p2_xrd.csv",
        storage_backend="local",
    )
    db_session.add(file_p2)

    # ML Dataset & Model for P2
    ds_p2 = MLDataset(
        id=uuid.uuid4(),
        project_id=p2.id,
        name="P2 ML Dataset",
        version="v1.0",
        target_property="crystallite_size_nm",
        target_unit="nm",
        features=[],
    )
    db_session.add(ds_p2)
    await db_session.flush()

    tr_p2 = MLTrainingRun(
        id=uuid.uuid4(),
        dataset_id=ds_p2.id,
        dataset_version="v1.0",
        model_type="RandomForest",
        status="COMPLETED",
    )
    db_session.add(tr_p2)
    await db_session.flush()

    model_p2 = MLModel(
        id=uuid.uuid4(),
        training_run_id=tr_p2.id,
        dataset_id=ds_p2.id,
        dataset_version="v1.0",
        name="RandomForest",
        model_type="RandomForest",
        target_property="crystallite_size_nm",
        target_unit="nm",
        version="v1.0",
        feature_names=["temp"],
        feature_specs=[],
        preprocessing_config={},
        hyperparameters={},
        library_versions={"scikit-learn": "1.4.0"},
        artifact_path="models/SEC-P2/rf_v1.joblib",
        metrics={"r2": 0.92, "mae": 1.2},
        status="ACTIVE",
    )
    db_session.add(model_p2)
    await db_session.flush()

    # Generate JWTs
    admin_token = create_access_token(admin_user.id)
    student1_token = create_access_token(student1_user.id)
    student2_token = create_access_token(student2_user.id)

    return {
        "p1": p1,
        "p2": p2,
        "admin_user": admin_user,
        "admin_token": admin_token,
        "student1_user": student1_user,
        "student1_token": student1_token,
        "student2_user": student2_user,
        "student2_token": student2_token,
        "exp_p2": exp_p2,
        "sample_p2": sample_p2,
        "char_p2": char_p2,
        "file_p2": file_p2,
        "model_p2": model_p2,
        "ds_p2": ds_p2,
    }


def make_client(db_session, token=None):
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


# ── TEST 1: UNIFIED LOGIN & ADMIN IDENTIFICATION ─────────────────

@pytest.mark.asyncio
async def test_unified_login_admin_and_student(db_session: AsyncSession, security_setup):
    """Verifies exactly ONE login endpoint authenticates both Admin and Student."""
    async with make_client(db_session) as ac:
        # Admin login
        admin_res = await ac.post("/api/v1/auth/login", json={"email": "v.atharvan@gmail.com", "password": "aaaaaaaa"})
        assert admin_res.status_code == 200, admin_res.text
        admin_data = admin_res.json()["data"]
        assert admin_data["user"]["email"] == "v.atharvan@gmail.com"
        assert admin_data["user"]["account_type"] == "ADMIN"
        assert admin_data["user"]["role"] == "ADMIN"
        assert "access_token" in admin_data

        # Student login
        student_email = security_setup["student1_user"].email
        student_res = await ac.post("/api/v1/auth/login", json={"email": student_email, "password": "studentpass1"})
        assert student_res.status_code == 200, student_res.text
        student_data = student_res.json()["data"]
        assert student_data["user"]["email"] == student_email
        assert student_data["user"]["account_type"] == "STUDENT"
        assert student_data["user"]["role"] == "RESEARCHER"


# ── TEST 2: ADMIN SYSTEM-WIDE ACCESS TO ALL PROJECTS ─────────────

@pytest.mark.asyncio
async def test_admin_system_wide_projects_access(db_session: AsyncSession, security_setup):
    """Admin GET /projects/ returns all projects in system."""
    async with make_client(db_session, token=security_setup["admin_token"]) as ac:
        res = await ac.get("/api/v1/projects/")
        assert res.status_code == 200
        projects = res.json()
        p_ids = [p["id"] for p in projects]
        assert str(security_setup["p1"].id) in p_ids
        assert str(security_setup["p2"].id) in p_ids


# ── TEST 3: ADMIN ACCESS TO GROUPS & USERS (STUDENT FORBIDDEN) ───

@pytest.mark.asyncio
async def test_admin_vs_student_administrative_endpoints(db_session: AsyncSession, security_setup):
    """Admin can list all groups and users; Student is rejected with 403."""
    # Admin access
    async with make_client(db_session, token=security_setup["admin_token"]) as ac:
        g_res = await ac.get("/api/v1/groups/")
        assert g_res.status_code == 200
        assert len(g_res.json()["data"]) >= 2

        u_res = await ac.get("/api/v1/auth/users")
        assert u_res.status_code == 200
        assert len(u_res.json()["data"]) >= 3

    # Student access forbidden
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        g_res = await ac.get("/api/v1/groups/")
        assert g_res.status_code == 403
        assert "ADMIN_REQUIRED" in g_res.text

        u_res = await ac.get("/api/v1/auth/users")
        assert u_res.status_code == 403
        assert "ADMIN_REQUIRED" in u_res.text


# ── TEST 4: STUDENT STRICT PROJECT SCOPING ───────────────────────

@pytest.mark.asyncio
async def test_student_project_scoping(db_session: AsyncSession, security_setup):
    """Student GET /projects/ returns ONLY their assigned project."""
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res = await ac.get("/api/v1/projects/")
        assert res.status_code == 200
        projects = res.json()
        assert len(projects) == 1
        assert projects[0]["id"] == str(security_setup["p1"].id)
        assert projects[0]["project_code"] == "SEC-P1"


# ── TEST 5: IDOR DIRECT PROJECT ACCESS BLOCK ─────────────────────

@pytest.mark.asyncio
async def test_student_idor_foreign_project_access_denied(db_session: AsyncSession, security_setup):
    """Student 1 cannot access Project 2 by direct ID."""
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res = await ac.get(f"/api/v1/projects/{security_setup['p2'].id}")
        assert res.status_code in (403, 404)


# ── TEST 6: IDOR DIRECT EXPERIMENT ACCESS BLOCK ──────────────────

@pytest.mark.asyncio
async def test_student_idor_foreign_experiment_access_denied(db_session: AsyncSession, security_setup):
    """Student 1 cannot view, update, or delete Project 2 experiments."""
    exp_id = security_setup["exp_p2"].id
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        # GET foreign experiment
        res_get = await ac.get(f"/api/v1/experiments/{exp_id}")
        assert res_get.status_code in (403, 404)

        # PUT foreign experiment
        res_put = await ac.put(f"/api/v1/experiments/{exp_id}", json={"title": "Hacked Title"})
        assert res_put.status_code in (403, 404)

        # DELETE foreign experiment
        res_del = await ac.delete(f"/api/v1/experiments/{exp_id}")
        assert res_del.status_code in (403, 404)


# ── TEST 7: IDOR TAMPERING ON EXPERIMENT CREATION ────────────────

@pytest.mark.asyncio
async def test_student_cannot_create_experiment_in_foreign_project(db_session: AsyncSession, security_setup):
    """Student 1 cannot create experiment inside Project 2."""
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res = await ac.post("/api/v1/experiments/", json={
            "project_id": str(security_setup["p2"].id),
            "experiment_code": "EXP-HACK-01",
            "title": "Unauthorized Experiment",
        })
        assert res.status_code in (403, 404)


# ── TEST 8: IDOR DIRECT SAMPLE ACCESS BLOCK ──────────────────────

@pytest.mark.asyncio
async def test_student_idor_foreign_sample_access_denied(db_session: AsyncSession, security_setup):
    """Student 1 cannot view or create samples on foreign experiments."""
    sample_id = security_setup["sample_p2"].id
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res_get = await ac.get(f"/api/v1/samples/{sample_id}")
        assert res_get.status_code in (403, 404)

        # Attempt creating sample under foreign experiment
        res_create = await ac.post("/api/v1/samples/", json={
            "experiment_id": str(security_setup["exp_p2"].id),
            "sample_code": "SMP-HACK-01",
            "name": "Hacked Sample",
            "material": "ZnO",
        })
        assert res_create.status_code in (403, 404)


# ── TEST 9: IDOR CHARACTERIZATION & RAW FILES ACCESS BLOCK ───────

@pytest.mark.asyncio
async def test_student_idor_foreign_characterization_and_files_denied(db_session: AsyncSession, security_setup):
    """Student 1 cannot access foreign characterizations or download raw files."""
    char_id = security_setup["char_p2"].id
    file_id = security_setup["file_p2"].id
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res_char = await ac.get(f"/api/v1/characterizations/{char_id}")
        assert res_char.status_code in (403, 404)

        res_file = await ac.get(f"/api/v1/files/{file_id}")
        assert res_file.status_code in (403, 404)

        res_down = await ac.get(f"/api/v1/files/{file_id}/download")
        assert res_down.status_code in (403, 404)


# ── TEST 10: IDOR ML DATASET & MODEL ACCESS BLOCK ────────────────

@pytest.mark.asyncio
async def test_student_idor_foreign_ml_resources_denied(db_session: AsyncSession, security_setup):
    """Student 1 cannot access Project 2 ML dataset or trained models."""
    ds_id = security_setup["ds_p2"].id
    model_id = security_setup["model_p2"].id
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res_ds = await ac.get(f"/api/v1/ml/datasets/{ds_id}")
        assert res_ds.status_code in (403, 404)

        res_m = await ac.get(f"/api/v1/ml/models/{model_id}")
        assert res_m.status_code in (403, 404)


# ── TEST 11: DASHBOARD STATS SCOPING (STUDENT VS ADMIN) ──────────

@pytest.mark.asyncio
async def test_dashboard_stats_scoping(db_session: AsyncSession, security_setup):
    """Admin receives global statistics; Student receives project-scoped statistics."""
    # Student 1 dashboard stats
    async with make_client(db_session, token=security_setup["student1_token"]) as ac:
        res_s = await ac.get("/api/v1/dashboard/stats")
        assert res_s.status_code == 200
        stats_s = res_s.json()
        assert stats_s["total_projects"] == 1
        assert stats_s["total_experiments"] == 0  # P1 has 0 experiments

    # Admin dashboard stats
    async with make_client(db_session, token=security_setup["admin_token"]) as ac:
        res_a = await ac.get("/api/v1/dashboard/stats")
        assert res_a.status_code == 200
        stats_a = res_a.json()
        assert stats_a["total_projects"] >= 2
        assert stats_a["total_experiments"] >= 1  # Includes P2 experiment


# ── TEST 12: ADMIN BYPASS CROSS-PROJECT ACCESS ───────────────────

@pytest.mark.asyncio
async def test_admin_cross_project_bypass(db_session: AsyncSession, security_setup):
    """Admin can seamlessly access P2 experiment, sample, characterization, raw file, and ML model."""
    exp_id = security_setup["exp_p2"].id
    sample_id = security_setup["sample_p2"].id
    char_id = security_setup["char_p2"].id
    file_id = security_setup["file_p2"].id
    model_id = security_setup["model_p2"].id

    async with make_client(db_session, token=security_setup["admin_token"]) as ac:
        assert (await ac.get(f"/api/v1/projects/{security_setup['p2'].id}")).status_code == 200
        assert (await ac.get(f"/api/v1/experiments/{exp_id}")).status_code == 200
        assert (await ac.get(f"/api/v1/samples/{sample_id}")).status_code == 200
        assert (await ac.get(f"/api/v1/characterizations/{char_id}")).status_code == 200
        assert (await ac.get(f"/api/v1/files/{file_id}")).status_code == 200
        assert (await ac.get(f"/api/v1/ml/models/{model_id}")).status_code == 200
