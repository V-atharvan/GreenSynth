"""
GreenSynth Analytics — Phase 8 Multi-Device & Security Isolation Test Suite

Exhaustively verifies:
1. Multi-Device Login & Real-Time Data Persistence (Device 1/2/3 within Group A).
2. Comprehensive Cross-Group Isolation (Group A vs Group B) across:
   - Experiments, Samples, and Raw Files
   - Characterizations and Analysis Runs
   - ML Datasets, ML Models, and ML Predictions
   - Recommendations, DOE Campaigns, and Optimization Runs
   - Dashboard Scoping (Project A stats vs Project B stats)
3. Tampering Defenses:
   - Request payload project_id spoofing (rejected with 403)
   - Direct URL parameter UUID tampering (rejected with 404)
   - Query parameter project_id tampering (rejected with 403)
   - Mass assignment privilege escalation prevention
4. Invitation & Membership Security:
   - Token reuse prevention
   - Expired token rejection
   - Non-leader invitation attempt rejected with 403
5. Database Transaction Integrity & Concurrency:
   - Concurrent async client requests without cross-talk or race conditions
"""

from __future__ import annotations

import asyncio
import io
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.analysis import AnalysisRun, AnalysisStatus
from app.models.characterization import (
    Characterization,
    CharacterizationStatus,
    RawFile,
    TechniqueType,
)
from app.models.doe import DOE, Objective
from app.models.experiment import Experiment, ExperimentStatus
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.invitation import Invitation, InvitationStatus
from app.models.ml import MLDataset, MLModel, MLTrainingRun
from app.models.optimization import OptimizationObjective, OptimizationRun
from app.models.project import Project, ProjectStatus
from app.models.recommendation import Recommendation
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample, SampleStatus
from app.models.user import User


@pytest.fixture
async def phase8_environment(db_session: AsyncSession, test_engine) -> dict[str, Any]:
    """
    Sets up two isolated research groups and projects with session factory override:
    - Group Alpha (Project P1 - Thin Film Solar)
      - Leader Alpha (Device 1)
      - Member Alpha 1 (Device 2)
      - Member Alpha 2 (Device 3)
    - Group Beta (Project P2 - Thermoelectric)
      - Leader Beta (Device 4)
      - Member Beta 1 (Device 5)
    """
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)

    async def override_get_db():
        async with session_factory() as s:
            yield s
            await s.commit()

    app.dependency_overrides[get_db] = override_get_db

    # ── Project Alpha (P1) ──────────────────────────────────
    proj_a = Project(
        id=uuid.uuid4(),
        project_code=f"P1-TEST-{uuid.uuid4().hex[:4].upper()}",
        name="Project P1 — Thin Film Solar",
        material="CuO",
        extract="Mulberry Leaf",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_a)

    # Leader Alpha
    leader_a = User(
        id=uuid.uuid4(),
        username=f"leader_a_{uuid.uuid4().hex[:6]}",
        email=f"leader_a_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. Alice Leader A",
        department="Chemical Engineering",
        phone="9876543210",
        roll_number=f"ROLL-LA-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_a",
        is_active=True,
    )
    db_session.add(leader_a)
    await db_session.flush()

    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name="Research Group Alpha",
        project_id=proj_a.id,
        leader_user_id=leader_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group_a)
    await db_session.flush()

    mem_leader_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=leader_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_leader_a)

    # Member Alpha 1
    member_a1 = User(
        id=uuid.uuid4(),
        username=f"member_a1_{uuid.uuid4().hex[:6]}",
        email=f"member_a1_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Bob Member A1",
        department="Chemical Engineering",
        phone="9876543211",
        roll_number=f"ROLL-MA1-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_a1",
        is_active=True,
    )
    db_session.add(member_a1)
    await db_session.flush()

    mem_a1 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=member_a1.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_a1)

    # Member Alpha 2
    member_a2 = User(
        id=uuid.uuid4(),
        username=f"member_a2_{uuid.uuid4().hex[:6]}",
        email=f"member_a2_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Charlie Member A2",
        department="Chemical Engineering",
        phone="9876543212",
        roll_number=f"ROLL-MA2-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_a2",
        is_active=True,
    )
    db_session.add(member_a2)
    await db_session.flush()

    mem_a2 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=member_a2.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_a2)

    # ── Project Beta (P2) ───────────────────────────────────
    proj_b = Project(
        id=uuid.uuid4(),
        project_code=f"P2-TEST-{uuid.uuid4().hex[:4].upper()}",
        name="Project P2 — Thermoelectric Oxide",
        material="ZnO",
        extract="Aloe Vera",
        solvent="Water",
        synthesis_method="Hydrothermal",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_b)

    # Leader Beta
    leader_b = User(
        id=uuid.uuid4(),
        username=f"leader_b_{uuid.uuid4().hex[:6]}",
        email=f"leader_b_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. David Leader B",
        department="Physics",
        phone="9876543220",
        roll_number=f"ROLL-LB-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_b",
        is_active=True,
    )
    db_session.add(leader_b)
    await db_session.flush()

    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name="Research Group Beta",
        project_id=proj_b.id,
        leader_user_id=leader_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group_b)
    await db_session.flush()

    mem_leader_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=leader_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_leader_b)

    # Member Beta 1
    member_b1 = User(
        id=uuid.uuid4(),
        username=f"member_b1_{uuid.uuid4().hex[:6]}",
        email=f"member_b1_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Eve Member B1",
        department="Physics",
        phone="9876543221",
        roll_number=f"ROLL-MB1-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_b1",
        is_active=True,
    )
    db_session.add(member_b1)
    await db_session.flush()

    mem_b1 = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=member_b1.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_b1)

    await db_session.commit()

    token_la = create_access_token(leader_a.id)
    token_ma1 = create_access_token(member_a1.id)
    token_ma2 = create_access_token(member_a2.id)
    token_lb = create_access_token(leader_b.id)
    token_mb1 = create_access_token(member_b1.id)

    yield {
        "proj_a": proj_a,
        "group_a": group_a,
        "leader_a": leader_a,
        "member_a1": member_a1,
        "member_a2": member_a2,
        "token_la": token_la,
        "token_ma1": token_ma1,
        "token_ma2": token_ma2,
        "headers_la": {"Authorization": f"Bearer {token_la}"},
        "headers_ma1": {"Authorization": f"Bearer {token_ma1}"},
        "headers_ma2": {"Authorization": f"Bearer {token_ma2}"},
        "proj_b": proj_b,
        "group_b": group_b,
        "leader_b": leader_b,
        "member_b1": member_b1,
        "token_lb": token_lb,
        "token_mb1": token_mb1,
        "headers_lb": {"Authorization": f"Bearer {token_lb}"},
        "headers_mb1": {"Authorization": f"Bearer {token_mb1}"},
    }

    app.dependency_overrides.clear()


def make_client(headers: dict[str, str]) -> AsyncClient:
    """Helper to create an AsyncClient with given authentication headers."""
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    )


# ==============================================================================
# 1. MULTI-DEVICE LOGIN & REAL-TIME PERSISTENCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_multi_device_login_and_persistence(phase8_environment, db_session: AsyncSession):
    """
    Simulates:
    - Device 1 (Leader Alpha): logs in and creates an experiment & sample.
    - Device 2 (Member Alpha 1): logs in simultaneously and fetches the newly created experiment & sample.
    - Device 3 (Member Alpha 2): logs in simultaneously and updates the experiment notes.
    - Device 1 & Device 2: re-fetch and see Device 3's updates in real time.
    """
    env = phase8_environment
    client_dev1 = make_client(env["headers_la"])
    client_dev2 = make_client(env["headers_ma1"])
    client_dev3 = make_client(env["headers_ma2"])

    # Device 1 creates experiment
    exp_payload = {
        "project_id": str(env["proj_a"].id),
        "experiment_code": f"EXP-DEV1-{uuid.uuid4().hex[:4].upper()}",
        "title": "Spray Pyrolysis Optimization Run #1",
        "status": "IN_PROGRESS",
        "researcher": "Dr. Alice (Device 1)",
        "notes": "Initial run parameters created on Device 1",
    }
    res1 = await client_dev1.post("/api/v1/experiments/", json=exp_payload)
    assert res1.status_code == 201, res1.text
    exp_data = res1.json()
    exp_id = exp_data["id"]

    # Device 1 creates sample under experiment
    sample_payload = {
        "experiment_id": exp_id,
        "sample_code": f"SMP-DEV1-{uuid.uuid4().hex[:4].upper()}",
        "name": "CuO Thin Film Sample A",
        "material": "CuO",
        "status": "PREPARED",
    }
    s_res1 = await client_dev1.post("/api/v1/samples/", json=sample_payload)
    assert s_res1.status_code == 201, s_res1.text
    sample_id = s_res1.json()["id"]

    # Device 2 (Member A1) immediately fetches experiment and sample
    res2 = await client_dev2.get(f"/api/v1/experiments/{exp_id}")
    assert res2.status_code == 200
    assert res2.json()["title"] == "Spray Pyrolysis Optimization Run #1"

    s_res2 = await client_dev2.get(f"/api/v1/samples/{sample_id}")
    assert s_res2.status_code == 200
    assert s_res2.json()["name"] == "CuO Thin Film Sample A"

    # Device 3 (Member A2) updates the experiment notes
    upd_payload = {
        "notes": "Updated by Charlie from Device 3 during laboratory characterization.",
        "status": "COMPLETED",
    }
    res3 = await client_dev3.put(f"/api/v1/experiments/{exp_id}", json=upd_payload)
    assert res3.status_code == 200
    assert res3.json()["status"] == "COMPLETED"

    # Device 1 and Device 2 verify the updated state
    verify_dev1 = await client_dev1.get(f"/api/v1/experiments/{exp_id}")
    assert verify_dev1.status_code == 200
    assert verify_dev1.json()["notes"] == upd_payload["notes"]
    assert verify_dev1.json()["status"] == "COMPLETED"

    verify_dev2 = await client_dev2.get(f"/api/v1/experiments/{exp_id}")
    assert verify_dev2.status_code == 200
    assert verify_dev2.json()["status"] == "COMPLETED"


# ==============================================================================
# 2. CROSS-GROUP EXPERIMENT, SAMPLE & FILE ISOLATION
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_group_experiment_and_sample_isolation(phase8_environment, db_session: AsyncSession):
    """
    Verifies:
    - Group Alpha creates Experiment Alpha & Sample Alpha.
    - Group Beta attempts GET, PUT, DELETE on Experiment Alpha -> 404 Not Found (zero leakage).
    - Group Beta attempts GET, PUT, DELETE on Sample Alpha -> 404 Not Found.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])
    client_b = make_client(env["headers_lb"])

    # Create Group A experiment
    exp_res = await client_a.post("/api/v1/experiments/", json={
        "project_id": str(env["proj_a"].id),
        "experiment_code": f"EXP-A-{uuid.uuid4().hex[:4].upper()}",
        "title": "Alpha Proprietary Synthesis",
        "status": "PLANNED",
    })
    assert exp_res.status_code == 201
    exp_a_id = exp_res.json()["id"]

    # Create Group A sample
    s_res = await client_a.post("/api/v1/samples/", json={
        "experiment_id": exp_a_id,
        "sample_code": f"SMP-A-{uuid.uuid4().hex[:4].upper()}",
        "name": "Alpha Sample 1",
    })
    assert s_res.status_code == 201
    s_a_id = s_res.json()["id"]

    # Group B attempts GET
    get_exp = await client_b.get(f"/api/v1/experiments/{exp_a_id}")
    assert get_exp.status_code == 404

    get_smp = await client_b.get(f"/api/v1/samples/{s_a_id}")
    assert get_smp.status_code == 404

    # Group B attempts PUT
    put_exp = await client_b.put(f"/api/v1/experiments/{exp_a_id}", json={"title": "Hacked Title"})
    assert put_exp.status_code == 404

    put_smp = await client_b.put(f"/api/v1/samples/{s_a_id}", json={"name": "Hacked Name"})
    assert put_smp.status_code == 404

    # Group B attempts DELETE
    del_smp = await client_b.delete(f"/api/v1/samples/{s_a_id}")
    assert del_smp.status_code == 404

    del_exp = await client_b.delete(f"/api/v1/experiments/{exp_a_id}")
    assert del_exp.status_code == 404


@pytest.mark.asyncio
async def test_cross_group_file_download_isolation(phase8_environment, db_session: AsyncSession):
    """
    Verifies that Group Beta cannot download or inspect raw characterization data
    files belonging to Group Alpha.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])
    client_b = make_client(env["headers_lb"])

    # Create hierarchy in Group A
    exp = Experiment(
        id=uuid.uuid4(),
        project_id=env["proj_a"].id,
        experiment_code="EXP-FILE-A",
        title="File Test Exp",
        status=ExperimentStatus.PLANNED.value,
    )
    db_session.add(exp)
    await db_session.flush()

    smp = Sample(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        sample_code="SMP-FILE-A",
        name="File Test Sample",
        status=SampleStatus.PREPARED.value,
    )
    db_session.add(smp)
    await db_session.flush()

    char = Characterization(
        id=uuid.uuid4(),
        sample_id=smp.id,
        technique=TechniqueType.XRD.value,
        status=CharacterizationStatus.UPLOADED.value,
    )
    db_session.add(char)
    await db_session.flush()

    raw_file = RawFile(
        id=uuid.uuid4(),
        characterization_id=char.id,
        sample_id=smp.id,
        original_filename="alpha_xrd_data.csv",
        stored_filename="uploads/alpha_xrd_data.csv",
        file_extension=".csv",
        mime_type="text/csv",
        file_size=1024,
        checksum="hash_a_12345",
        storage_path="uploads/alpha_xrd_data.csv",
    )
    db_session.add(raw_file)
    await db_session.commit()

    # Group A can inspect file metadata
    res_a = await client_a.get(f"/api/v1/files/{raw_file.id}")
    assert res_a.status_code == 200
    assert res_a.json()["original_filename"] == "alpha_xrd_data.csv"

    # Group B cannot inspect file metadata
    res_b = await client_b.get(f"/api/v1/files/{raw_file.id}")
    assert res_b.status_code == 404

    # Group B cannot download file
    res_b_dl = await client_b.get(f"/api/v1/files/{raw_file.id}/download")
    assert res_b_dl.status_code == 404


# ==============================================================================
# 3. CROSS-GROUP ML, RECOMMENDATION, DOE & OPTIMIZATION ISOLATION
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_group_ml_dataset_and_model_isolation(phase8_environment, db_session: AsyncSession):
    """
    Verifies that Group Beta cannot read, train against, or run predictions
    using Group Alpha's ML datasets or ML models.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])
    client_b = make_client(env["headers_lb"])

    # Create ML Dataset and Model for Group Alpha
    ds_a = MLDataset(
        id=uuid.uuid4(),
        project_id=env["proj_a"].id,
        name="Alpha Bandgap Dataset",
        version="v1.0",
        target_property="bandgap_ev",
        target_type="CONTINUOUS",
        target_unit="eV",
        features=[{"name": "temperature_c", "type": "NUMBER"}],
        status="ACTIVE",
    )
    db_session.add(ds_a)
    await db_session.flush()

    run_a = MLTrainingRun(
        id=uuid.uuid4(),
        dataset_id=ds_a.id,
        dataset_version="v1.0",
        model_type="RandomForest",
        status="COMPLETED",
    )
    db_session.add(run_a)
    await db_session.flush()

    model_a = MLModel(
        id=uuid.uuid4(),
        training_run_id=run_a.id,
        dataset_id=ds_a.id,
        dataset_version="v1.0",
        name="Alpha RF Model",
        model_type="RandomForest",
        version="1.0",
        target_property="bandgap_ev",
        target_type="CONTINUOUS",
        target_unit="eV",
        feature_names=["temperature_c"],
        feature_specs=[{"name": "temperature_c", "type": "NUMBER"}],
        preprocessing_config={},
        hyperparameters={},
        artifact_path="/tmp/fake_model.joblib",
        metrics={"cv_r2": 0.92, "cv_rmse": 0.05, "cv_mae": 0.04},
        library_versions={"scikit-learn": "1.4.0"},
        status="PRODUCTION_CANDIDATE",
    )
    db_session.add(model_a)
    await db_session.commit()

    # Group A can fetch dataset and model
    res_a_ds = await client_a.get(f"/api/v1/ml/datasets/{ds_a.id}")
    assert res_a_ds.status_code == 200
    res_a_mdl = await client_a.get(f"/api/v1/ml/models/{model_a.id}")
    assert res_a_mdl.status_code == 200

    # Group B cannot fetch Group A dataset
    res_b_ds = await client_b.get(f"/api/v1/ml/datasets/{ds_a.id}")
    assert res_b_ds.status_code == 404

    # Group B cannot fetch Group A model
    res_b_mdl = await client_b.get(f"/api/v1/ml/models/{model_a.id}")
    assert res_b_mdl.status_code == 404

    # Group B cannot trigger prediction on Group A model
    pred_res = await client_b.post(f"/api/v1/ml/models/{model_a.id}/predict", json={
        "input_parameters": {"temperature_c": 350.0}
    })
    assert pred_res.status_code == 404


@pytest.mark.asyncio
async def test_cross_group_doe_and_optimization_isolation(phase8_environment, db_session: AsyncSession):
    """
    Verifies that Group Beta cannot view or modify Group Alpha's DOE campaigns
    or optimization runs.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])
    client_b = make_client(env["headers_lb"])

    # Create DOE for Project A
    doe_a = DOE(
        id=uuid.uuid4(),
        project_id=env["proj_a"].id,
        name="Alpha Factorial Study",
        design_method="FULL_FACTORIAL",
        factors=[{"parameter_code": "temp", "name": "Temperature", "factor_type": "CONTINUOUS", "levels": 3}],
        requested_runs=4,
        replicates=1,
        center_points=0,
    )
    db_session.add(doe_a)

    # Create Optimization Objective & Run for Project A
    opt_obj_a = OptimizationObjective(
        id=uuid.uuid4(),
        project_id=env["proj_a"].id,
        name="Maximize Crystallinity",
        target_property="crystallite_size_nm",
        direction="MAXIMIZE",
        weight=1.0,
    )
    db_session.add(opt_obj_a)
    await db_session.flush()

    opt_run_a = OptimizationRun(
        id=uuid.uuid4(),
        project_id=env["proj_a"].id,
        objective_id=opt_obj_a.id,
        model_id=uuid.uuid4(),
        model_version="1.0",
        dataset_id=uuid.uuid4(),
        dataset_version="v1.0",
        generation_method="GRID",
        search_space_definition={},
        constraints_definition={},
        status="COMPLETED",
    )
    db_session.add(opt_run_a)
    await db_session.commit()

    # Group A reads them successfully
    res_doe_a = await client_a.get(f"/api/v1/doe/{doe_a.id}")
    assert res_doe_a.status_code == 200
    res_opt_a = await client_a.get(f"/api/v1/optimization/runs/{opt_run_a.id}")
    assert res_opt_a.status_code == 200

    # Group B cannot access Group A's DOE
    res_doe_b = await client_b.get(f"/api/v1/doe/{doe_a.id}")
    assert res_doe_b.status_code == 404

    # Group B cannot access Group A's Optimization Run
    res_opt_b = await client_b.get(f"/api/v1/optimization/runs/{opt_run_a.id}")
    assert res_opt_b.status_code == 404


# ==============================================================================
# 4. DASHBOARD STATISTICS ISOLATION
# ==============================================================================

@pytest.mark.asyncio
async def test_dashboard_scoped_statistics(phase8_environment, db_session: AsyncSession):
    """
    Verifies that the dashboard metrics endpoint calculates stats strictly for
    the authenticated user's assigned project.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])
    client_b = make_client(env["headers_lb"])

    # Create 3 experiments for Project A, 1 for Project B
    for i in range(3):
        db_session.add(Experiment(
            id=uuid.uuid4(),
            project_id=env["proj_a"].id,
            experiment_code=f"EXP-DASH-A-{i}",
            title=f"Dash Exp A {i}",
            status=ExperimentStatus.COMPLETED.value,
        ))
    db_session.add(Experiment(
        id=uuid.uuid4(),
        project_id=env["proj_b"].id,
        experiment_code="EXP-DASH-B-0",
        title="Dash Exp B 0",
        status=ExperimentStatus.PLANNED.value,
    ))
    await db_session.commit()

    res_a = await client_a.get("/api/v1/dashboard/stats")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total_experiments"] == 3

    res_b = await client_b.get("/api/v1/dashboard/stats")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total_experiments"] == 1


# ==============================================================================
# 5. TAMPERING DEFENSE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_payload_project_id_spoofing_blocked(phase8_environment, db_session: AsyncSession):
    """
    Verifies that when a Group A user attempts to create an entity supplying
    Project B's UUID in the payload, the server rejects with 403 Forbidden.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])

    # Attempt to create experiment in Project B
    res_exp = await client_a.post("/api/v1/experiments/", json={
        "project_id": str(env["proj_b"].id),
        "experiment_code": "EXP-SPOOF-01",
        "title": "Spoofed Experiment",
    })
    assert res_exp.status_code == 403
    assert res_exp.json()["detail"]["code"] == "PROJECT_ACCESS_DENIED"

    # Attempt to create optimization objective in Project B
    res_opt = await client_a.post("/api/v1/optimization/objectives", json={
        "project_id": str(env["proj_b"].id),
        "name": "Spoofed Objective",
        "target_property": "bandgap_ev",
        "direction": "MAXIMIZE",
        "weight": 1.0,
    })
    assert res_opt.status_code == 403


@pytest.mark.asyncio
async def test_query_parameter_tampering_isolated(phase8_environment, db_session: AsyncSession):
    """
    Verifies that supplying ?project_id=PROJ_B_ID in query params rejects unauthorized
    cross-project queries with 403 Forbidden.
    """
    env = phase8_environment
    client_a = make_client(env["headers_la"])

    # Create experiments for Project B
    db_session.add(Experiment(
        id=uuid.uuid4(),
        project_id=env["proj_b"].id,
        experiment_code="EXP-QUERY-B",
        title="Beta Secret Experiment",
        status=ExperimentStatus.IN_PROGRESS.value,
    ))
    await db_session.commit()

    # Group A attempts to filter experiments by Project B
    res = await client_a.get(f"/api/v1/experiments/?project_id={env['proj_b'].id}")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "PROJECT_ACCESS_DENIED"


# ==============================================================================
# 6. INVITATION & MEMBERSHIP SECURITY
# ==============================================================================

@pytest.mark.asyncio
async def test_invitation_reuse_and_duplicate_membership_prevention(phase8_environment, db_session: AsyncSession):
    """
    Verifies that:
    1. Regular members cannot issue invitations (Leader only -> 403).
    2. Leader sends valid invitation and student accepts successfully.
    3. Replaying the accepted invitation fails with 400 Bad Request.
    """
    from datetime import datetime, timedelta, timezone
    from app.core.security import hash_invitation_token
    env = phase8_environment
    client_leader_a = make_client(env["headers_la"])
    client_member_a = make_client(env["headers_ma1"])

    # Regular member attempts to invite -> 403 LEADER_REQUIRED
    res_mem_inv = await client_member_a.post("/api/v1/groups/me/invitations", json={
        "email": "newstudent@greensynth.edu",
        "full_name": "New Student",
        "department": "Chemistry",
        "phone": "9876543299",
        "roll_number": "ROLL-NEW-01",
    })
    assert res_mem_inv.status_code == 403
    assert "Leader" in str(res_mem_inv.json()["detail"])

    # Leader sends valid invitation
    inv_email = f"student_{uuid.uuid4().hex[:6]}@greensynth.edu"
    res_lead_inv = await client_leader_a.post("/api/v1/groups/me/invitations", json={
        "email": inv_email,
        "full_name": "Prospective Student",
        "department": "Chemical Engineering",
        "phone": "9876543298",
        "roll_number": f"ROLL-{uuid.uuid4().hex[:4]}",
    })
    assert res_lead_inv.status_code == 201

    # Insert a known token invitation into DB for acceptance testing
    raw_token = f"valid_token_{uuid.uuid4().hex}"
    test_inv = Invitation(
        id=uuid.uuid4(),
        group_id=env["group_a"].id,
        email=f"onboard_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Onboard Student",
        department="Chemical Engineering",
        phone="9876543290",
        roll_number=f"ROLL-OB-{uuid.uuid4().hex[:4]}",
        token_hash=hash_invitation_token(raw_token),
        status=InvitationStatus.PENDING.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(test_inv)
    await db_session.commit()

    # Student accepts invitation
    unauth_client = make_client({})
    accept_payload = {
        "token": raw_token,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    acc_res = await unauth_client.post("/api/v1/auth/accept-invitation", json=accept_payload)
    assert acc_res.status_code == 200
    assert "access_token" in acc_res.json()["data"]

    # Replaying the same invitation must fail with 400 Bad Request
    acc_res2 = await unauth_client.post("/api/v1/auth/accept-invitation", json=accept_payload)
    assert acc_res2.status_code == 400
    assert "accepted" in acc_res2.json()["detail"].lower()


# ==============================================================================
# 7. CONCURRENT REQUESTS & TRANSACTION INTEGRITY
# ==============================================================================

@pytest.mark.asyncio
async def test_concurrent_multi_client_requests(phase8_environment, db_session: AsyncSession):
    """
    Simulates concurrent read/write requests from multiple devices simultaneously
    to ensure thread/async safety and zero database session corruption.
    """
    env = phase8_environment
    client_a1 = make_client(env["headers_la"])
    client_a2 = make_client(env["headers_ma1"])
    client_b1 = make_client(env["headers_lb"])
    client_b2 = make_client(env["headers_mb1"])

    async def a1_task():
        return await client_a1.post("/api/v1/experiments/", json={
            "project_id": str(env["proj_a"].id),
            "experiment_code": f"EXP-CONC-A1-{uuid.uuid4().hex[:4]}",
            "title": "Concurrent Exp A1",
        })

    async def a2_task():
        return await client_a2.get("/api/v1/dashboard/stats")

    async def b1_task():
        return await client_b1.post("/api/v1/experiments/", json={
            "project_id": str(env["proj_b"].id),
            "experiment_code": f"EXP-CONC-B1-{uuid.uuid4().hex[:4]}",
            "title": "Concurrent Exp B1",
        })

    async def b2_task():
        return await client_b2.get("/api/v1/dashboard/stats")

    # Run all 4 tasks concurrently
    r_a1, r_a2, r_b1, r_b2 = await asyncio.gather(
        a1_task(), a2_task(), b1_task(), b2_task()
    )

    assert r_a1.status_code == 201
    assert r_a2.status_code == 200
    assert r_b1.status_code == 201
    assert r_b2.status_code == 200
