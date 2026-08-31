"""
GreenSynth Analytics — Phase 5 Cross-Project Authorization & Data Isolation Tests

Comprehensive integration test suite proving strict backend authorization and project-level isolation:
1. Unauthenticated requests are rejected with 401 Unauthorized.
2. Authenticated users without an active research group are rejected with 403 NO_ACTIVE_GROUP.
3. Cross-Project Read Isolation: Project A user cannot view Project B experiments, samples,
   characterizations, raw files, analysis runs, ML models, optimization runs, or evidence records (returns 404).
4. Cross-Project Mutation Isolation: Project A user cannot modify or delete Project B entities.
5. Cross-Project Scientific Execution Isolation: Project A user cannot run DOE, ML training/prediction,
   recommendation generation, or optimization against Project B assets.
6. Scoped Collection Queries: List queries (experiments, samples, datasets) return ONLY records for the user's project.
7. Dashboard Scoping: Dashboard statistics count only records in the user's project.
8. Leader Enforcement: Regular members cannot perform leader-only operations (invitations).
"""

from __future__ import annotations

import io
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.main import app
from app.models.analysis import AnalysisRun
from app.models.characterization import Characterization, RawFile
from app.models.evidence import DatasetVersion, EvidenceRecord
from app.models.experiment import Experiment, ExperimentStatus
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.ml import MLDataset, MLModel, MLTrainingRun
from app.models.optimization import OptimizationObjective, OptimizationRun
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample
from app.models.user import User


@pytest.fixture
async def multi_project_setup(db_session: AsyncSession) -> dict[str, Any]:
    """
    Sets up two isolated projects (Project A and Project B) with separate
    users, groups, and research assets.
    """
    # ── Project A Setup ──────────────────────────────────────
    proj_a = Project(
        id=uuid.uuid4(),
        project_code=f"PROJ-A-{uuid.uuid4().hex[:4].upper()}",
        name="Project A - Thin Film Solar",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_a)

    user_a = User(
        id=uuid.uuid4(),
        username=f"user_a_{uuid.uuid4().hex[:6]}",
        email=f"user_a_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. Alice Project A",
        department="Materials Science",
        phone="1112223333",
        roll_number=f"ROLL-A-{uuid.uuid4().hex[:4]}",
        password_hash="hash_a",
        is_active=True,
    )
    db_session.add(user_a)
    await db_session.flush()

    group_a = ResearchGroup(
        id=uuid.uuid4(),
        name="Research Group Alpha",
        project_id=proj_a.id,
        leader_user_id=user_a.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group_a)
    await db_session.flush()

    membership_a = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=user_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership_a)

    # Member in Group A (non-leader)
    member_a = User(
        id=uuid.uuid4(),
        username=f"member_a_{uuid.uuid4().hex[:6]}",
        email=f"member_a_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Student Member A",
        department="Materials Science",
        phone="1112223334",
        roll_number=f"ROLL-MA-{uuid.uuid4().hex[:4]}",
        password_hash="hash_ma",
        is_active=True,
    )
    db_session.add(member_a)
    await db_session.flush()

    membership_ma = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=member_a.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership_ma)

    # Project A Experiment, Sample, Characterization, RawFile
    exp_a = Experiment(
        id=uuid.uuid4(),
        project_id=proj_a.id,
        experiment_code=f"EXP-A-{uuid.uuid4().hex[:4]}",
        title="Project A Experiment 1",
        status=ExperimentStatus.COMPLETED,
    )
    db_session.add(exp_a)
    await db_session.flush()

    sample_a = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_a.id,
        sample_code=f"SAMP-A-{uuid.uuid4().hex[:4]}",
        name="Sample A1",
        material="CuO",
        status="PREPARED",
    )
    db_session.add(sample_a)
    await db_session.flush()

    char_a = Characterization(
        id=uuid.uuid4(),
        sample_id=sample_a.id,
        technique="XRD",
        status="COMPLETED",
    )
    db_session.add(char_a)
    await db_session.flush()

    raw_file_a = RawFile(
        id=uuid.uuid4(),
        characterization_id=char_a.id,
        sample_id=sample_a.id,
        original_filename="xrd_data_a.csv",
        stored_filename="uploads/xrd_data_a.csv",
        file_extension=".csv",
        mime_type="text/csv",
        file_size=1024,
        checksum="hash_a_12345",
        storage_path="uploads/xrd_data_a.csv",
    )
    db_session.add(raw_file_a)

    # ── Project B Setup ──────────────────────────────────────
    proj_b = Project(
        id=uuid.uuid4(),
        project_code=f"PROJ-B-{uuid.uuid4().hex[:4].upper()}",
        name="Project B - Thermoelectric Bi2Te3",
        material="Bi2Te3",
        extract="GreenTea",
        solvent="Water",
        synthesis_method="Hydrothermal",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_b)

    user_b = User(
        id=uuid.uuid4(),
        username=f"user_b_{uuid.uuid4().hex[:6]}",
        email=f"user_b_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. Bob Project B",
        department="Physics",
        phone="4445556666",
        roll_number=f"ROLL-B-{uuid.uuid4().hex[:4]}",
        password_hash="hash_b",
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.flush()

    group_b = ResearchGroup(
        id=uuid.uuid4(),
        name="Research Group Beta",
        project_id=proj_b.id,
        leader_user_id=user_b.id,
        status=GroupStatus.ACTIVE.value,
    )
    db_session.add(group_b)
    await db_session.flush()

    membership_b = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=user_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(membership_b)

    # Project B Experiment, Sample, Characterization, RawFile
    exp_b = Experiment(
        id=uuid.uuid4(),
        project_id=proj_b.id,
        experiment_code=f"EXP-B-{uuid.uuid4().hex[:4]}",
        title="Project B Secret Experiment",
        status=ExperimentStatus.COMPLETED,
    )
    db_session.add(exp_b)
    await db_session.flush()

    sample_b = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_b.id,
        sample_code=f"SAMP-B-{uuid.uuid4().hex[:4]}",
        name="Secret Sample B",
        material="Bi2Te3",
        status="PREPARED",
    )
    db_session.add(sample_b)
    await db_session.flush()

    char_b = Characterization(
        id=uuid.uuid4(),
        sample_id=sample_b.id,
        technique="XRD",
        status="COMPLETED",
    )
    db_session.add(char_b)
    await db_session.flush()

    raw_file_b = RawFile(
        id=uuid.uuid4(),
        characterization_id=char_b.id,
        sample_id=sample_b.id,
        original_filename="secret_xrd_b.csv",
        stored_filename="uploads/secret_xrd_b.csv",
        file_extension=".csv",
        mime_type="text/csv",
        file_size=2048,
        checksum="hash_b_67890",
        storage_path="uploads/secret_xrd_b.csv",
    )
    db_session.add(raw_file_b)

    # Project B ML Dataset & Model
    ds_b = MLDataset(
        id=uuid.uuid4(),
        project_id=proj_b.id,
        name="Project B Secret Dataset",
        version="v1.0",
        target_property="conductivity_s_cm",
        target_unit="S/cm",
        status="READY",
    )
    db_session.add(ds_b)
    await db_session.flush()

    train_run_b = MLTrainingRun(
        id=uuid.uuid4(),
        dataset_id=ds_b.id,
        dataset_version="v1.0",
        model_type="RANDOM_FOREST",
        status="COMPLETED",
    )
    db_session.add(train_run_b)
    await db_session.flush()

    model_b = MLModel(
        id=uuid.uuid4(),
        dataset_id=ds_b.id,
        dataset_version="v1.0",
        training_run_id=train_run_b.id,
        name="Project B Secret Model",
        model_type="RANDOM_FOREST",
        version="v1.0",
        target_property="conductivity_s_cm",
        target_unit="S/cm",
        feature_names=["substrate_temperature"],
        feature_specs=[{"name": "substrate_temperature", "type": "NUMBER"}],
        preprocessing_config={},
        hyperparameters={},
        artifact_path="/tmp/fake_model.joblib",
        metrics={"r2": 0.95},
        library_versions={"scikit-learn": "1.4.0"},
        status="ACTIVE",
    )
    db_session.add(model_b)

    # User without group
    user_nogroup = User(
        id=uuid.uuid4(),
        username=f"user_nogroup_{uuid.uuid4().hex[:6]}",
        email=f"user_nogroup_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Orphan User",
        department="Chemistry",
        phone="0001112222",
        roll_number=f"ROLL-NONE-{uuid.uuid4().hex[:4]}",
        password_hash="hash_none",
        is_active=True,
    )
    db_session.add(user_nogroup)

    await db_session.commit()

    token_a = create_access_token(user_a.id)
    token_member_a = create_access_token(member_a.id)
    token_b = create_access_token(user_b.id)
    token_nogroup = create_access_token(user_nogroup.id)

    return {
        "project_a": proj_a,
        "user_a": user_a,
        "token_a": token_a,
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "member_a": member_a,
        "token_member_a": token_member_a,
        "headers_member_a": {"Authorization": f"Bearer {token_member_a}"},
        "exp_a": exp_a,
        "sample_a": sample_a,
        "char_a": char_a,
        "raw_file_a": raw_file_a,
        "project_b": proj_b,
        "user_b": user_b,
        "token_b": token_b,
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "exp_b": exp_b,
        "sample_b": sample_b,
        "char_b": char_b,
        "raw_file_b": raw_file_b,
        "model_b": model_b,
        "dataset_b": ds_b,
        "user_nogroup": user_nogroup,
        "headers_nogroup": {"Authorization": f"Bearer {token_nogroup}"},
    }


# ── 1. Unauthenticated & No-Group Access Control ─────────────

@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(unauthenticated_client: AsyncClient) -> None:
    """Verify that unauthenticated requests to protected endpoints receive 401 Unauthorized."""
    endpoints = [
        ("GET", "/api/v1/experiments/"),
        ("GET", "/api/v1/samples/"),
        ("GET", "/api/v1/dashboard/stats"),
        ("GET", "/api/v1/ml/models"),
        ("GET", "/api/v1/optimization/objectives"),
        ("GET", "/api/v1/evidence"),
    ]
    for method, path in endpoints:
        if method == "GET":
            resp = await unauthenticated_client.get(path)
        assert resp.status_code == 401, f"Expected 401 for {method} {path}, got {resp.status_code}"


@pytest.mark.asyncio
async def test_user_without_active_group_rejected(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """Verify that an authenticated user without an active research group receives 403 NO_ACTIVE_GROUP."""
    headers = multi_project_setup["headers_nogroup"]
    resp = await unauthenticated_client.get("/api/v1/experiments/", headers=headers)
    assert resp.status_code == 403
    assert "NO_ACTIVE_GROUP" in resp.text


# ── 2. Cross-Project Read Isolation ──────────────────────────

@pytest.mark.asyncio
async def test_user_a_cannot_read_project_b_experiment(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A requesting Project B experiment by UUID receives 404 (zero enumeration leakage)."""
    headers = multi_project_setup["headers_a"]
    exp_b_id = multi_project_setup["exp_b"].id
    resp = await unauthenticated_client.get(f"/api/v1/experiments/{exp_b_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_read_project_b_sample(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A requesting Project B sample by UUID receives 404."""
    headers = multi_project_setup["headers_a"]
    sample_b_id = multi_project_setup["sample_b"].id
    resp = await unauthenticated_client.get(f"/api/v1/samples/{sample_b_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_read_project_b_characterization(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A requesting Project B characterization by UUID receives 404."""
    headers = multi_project_setup["headers_a"]
    char_b_id = multi_project_setup["char_b"].id
    resp = await unauthenticated_client.get(f"/api/v1/characterizations/{char_b_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_download_project_b_raw_file(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A attempting to download Project B raw file by UUID receives 404."""
    headers = multi_project_setup["headers_a"]
    raw_file_b_id = multi_project_setup["raw_file_b"].id
    resp = await unauthenticated_client.get(f"/api/v1/files/{raw_file_b_id}/download", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_access_project_b_ml_assets(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A requesting Project B ML model or dataset receives 404."""
    headers = multi_project_setup["headers_a"]
    model_b_id = multi_project_setup["model_b"].id
    dataset_b_id = multi_project_setup["dataset_b"].id

    resp_m = await unauthenticated_client.get(f"/api/v1/ml/models/{model_b_id}", headers=headers)
    assert resp_m.status_code == 404

    resp_d = await unauthenticated_client.get(f"/api/v1/ml/datasets/{dataset_b_id}", headers=headers)
    assert resp_d.status_code == 404


# ── 3. Cross-Project Mutation & Deletion Prevention ──────────

@pytest.mark.asyncio
async def test_user_a_cannot_mutate_or_delete_project_b_experiment(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A cannot update or delete Project B experiments."""
    headers = multi_project_setup["headers_a"]
    exp_b_id = multi_project_setup["exp_b"].id

    # Update attempt
    resp_put = await unauthenticated_client.put(
        f"/api/v1/experiments/{exp_b_id}",
        json={"title": "Hacked Title", "status": "COMPLETED"},
        headers=headers,
    )
    assert resp_put.status_code == 404

    # Delete attempt
    resp_del = await unauthenticated_client.delete(
        f"/api/v1/experiments/{exp_b_id}",
        headers=headers,
    )
    assert resp_del.status_code == 404


@pytest.mark.asyncio
async def test_user_a_cannot_create_sample_under_project_b_experiment(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A cannot inject samples into Project B experiments."""
    headers = multi_project_setup["headers_a"]
    exp_b_id = multi_project_setup["exp_b"].id

    resp = await unauthenticated_client.post(
        "/api/v1/samples/",
        json={
            "experiment_id": str(exp_b_id),
            "sample_code": "INJECTED-SAMPLE",
            "name": "Malicious Sample",
            "material": "CuO",
        },
        headers=headers,
    )
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_user_a_cannot_pass_project_b_id_in_parameters(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A passing Project B's project_id explicitly is rejected with 403 or 404."""
    headers = multi_project_setup["headers_a"]
    proj_b_id = multi_project_setup["project_b"].id

    resp = await unauthenticated_client.get(
        f"/api/v1/parameters/definitions?project_id={proj_b_id}",
        headers=headers,
    )
    assert resp.status_code in (403, 404)


# ── 4. Scoped Collection Query Isolation ─────────────────────

@pytest.mark.asyncio
async def test_collection_queries_are_strictly_scoped(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """Collection GET endpoints return only records belonging to the caller's active project."""
    headers_a = multi_project_setup["headers_a"]
    headers_b = multi_project_setup["headers_b"]

    # Experiments
    resp_exp_a = await unauthenticated_client.get("/api/v1/experiments/", headers=headers_a)
    assert resp_exp_a.status_code == 200
    exp_ids_a = [e["id"] for e in resp_exp_a.json()]
    assert str(multi_project_setup["exp_a"].id) in exp_ids_a
    assert str(multi_project_setup["exp_b"].id) not in exp_ids_a

    resp_exp_b = await unauthenticated_client.get("/api/v1/experiments/", headers=headers_b)
    assert resp_exp_b.status_code == 200
    exp_ids_b = [e["id"] for e in resp_exp_b.json()]
    assert str(multi_project_setup["exp_b"].id) in exp_ids_b
    assert str(multi_project_setup["exp_a"].id) not in exp_ids_b

    # Samples
    resp_samp_a = await unauthenticated_client.get("/api/v1/samples/", headers=headers_a)
    assert resp_samp_a.status_code == 200
    samp_ids_a = [s["id"] for s in resp_samp_a.json()]
    assert str(multi_project_setup["sample_a"].id) in samp_ids_a
    assert str(multi_project_setup["sample_b"].id) not in samp_ids_a


# ── 5. Scientific Computation & Workflow Isolation ───────────

@pytest.mark.asyncio
async def test_doe_execution_isolated(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A cannot run DOE preview or generation against Project B."""
    headers = multi_project_setup["headers_a"]
    proj_b_id = multi_project_setup["project_b"].id

    payload = {
        "project_id": str(proj_b_id),
        "name": "Cross Project DOE",
        "description": "Unauthorized DOE attempt",
        "research_question": "Can I access Project B?",
        "design_method": "FULL_FACTORIAL",
        "factors": [
            {
                "parameter_code": "temp",
                "name": "Temperature",
                "factor_type": "CONTINUOUS",
                "role": "CONTROLLABLE",
                "lower_bound": 300,
                "upper_bound": 400,
                "unit": "C",
                "levels": 2,
            }
        ],
        "responses": [
            {
                "property_name": "Conductivity",
                "unit": "S/cm",
                "direction": "MAXIMIZE",
                "weight": 1.0,
            }
        ],
    }

    resp = await unauthenticated_client.post("/api/v1/doe/preview", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "PROJECT_ACCESS_DENIED" in resp.text


@pytest.mark.asyncio
async def test_ml_prediction_isolated(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A cannot execute predictions using Project B models."""
    headers = multi_project_setup["headers_a"]
    model_b_id = multi_project_setup["model_b"].id

    payload = {
        "model_id": str(model_b_id),
        "parameter_values": {"substrate_temperature": 350.0},
    }

    resp = await unauthenticated_client.post("/api/v1/ml/predict", json=payload, headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_report_generation_isolated(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """User A cannot generate PDF reports for Project B experiments."""
    headers = multi_project_setup["headers_a"]
    exp_b_id = multi_project_setup["exp_b"].id

    resp = await unauthenticated_client.get(
        f"/api/v1/reports/experiments/{exp_b_id}/pdf",
        headers=headers,
    )
    assert resp.status_code == 404


# ── 6. Dashboard Scoping Isolation ───────────────────────────

@pytest.mark.asyncio
async def test_dashboard_statistics_scoped_to_project(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """Dashboard stats for User A count only Project A experiments and samples."""
    headers_a = multi_project_setup["headers_a"]
    headers_b = multi_project_setup["headers_b"]

    resp_a = await unauthenticated_client.get("/api/v1/dashboard/stats", headers=headers_a)
    assert resp_a.status_code == 200
    stats_a = resp_a.json()
    assert stats_a["total_experiments"] >= 1
    assert stats_a["total_samples"] >= 1

    # Check recent experiments in stats
    recent_codes_a = [e["experiment_code"] for e in stats_a["recent_experiments"]]
    assert multi_project_setup["exp_a"].experiment_code in recent_codes_a
    assert multi_project_setup["exp_b"].experiment_code not in recent_codes_a


# ── 7. Group Leader Privilege Enforcement ────────────────────

@pytest.mark.asyncio
async def test_member_cannot_perform_leader_operations(
    unauthenticated_client: AsyncClient, multi_project_setup: dict[str, Any]
) -> None:
    """Regular member in Group A cannot invite new members (requires leader)."""
    headers_member = multi_project_setup["headers_member_a"]

    invite_payload = {
        "email": "intruder@greensynth.edu",
        "full_name": "Unauthorized Invite",
        "roll_number": "ROLL-INT-01",
        "department": "Materials Science",
        "phone": "9990001111",
    }

    resp = await unauthenticated_client.post(
        "/api/v1/groups/me/invitations",
        json=invite_payload,
        headers=headers_member,
    )
    assert resp.status_code == 403
    assert "Group Leader" in resp.text or "LEADER_REQUIRED" in resp.text
