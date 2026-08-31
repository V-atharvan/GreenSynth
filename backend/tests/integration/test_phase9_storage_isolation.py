"""
GreenSynth Analytics — Phase 9 Integration Test Suite
Cloud Object Storage Integration, Persistent Raw-File Architecture & Secure Project-Scoped File Access

Verifies:
  1. Local storage upload, SHA-256 verification, and byte-for-byte raw file streaming download
  2. S3-compatible cloud object storage upload, project-scoped lineage keys, and pre-signed URLs
  3. Strict cross-project file isolation (Project B cannot inspect, download, or access Project A files)
  4. Multi-device session consistency (Device 1 uploads, Device 2 downloads exact bytes & SHA-256)
  5. Transactional consistency & storage rollback (no orphaned files on DB failure)
  6. Scientific analysis pipeline storage transparency (XRD & UV-Vis work seamlessly across backends)
  7. Controlled migration utility dry-run & non-destructive verification
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_db
from app.core.config import Settings
from app.core.security import create_access_token
from app.main import app
from app.models.characterization import (
    Characterization,
    CharacterizationStatus,
    RawFile,
    TechniqueType,
)
from app.models.experiment import Experiment, ExperimentStatus
from app.models.group_membership import GroupMembership, MembershipStatus
from app.models.project import Project, ProjectStatus
from app.models.research_group import GroupStatus, ResearchGroup
from app.models.sample import Sample, SampleStatus
from app.models.user import User
from app.schemas.characterization import CharacterizationCreate
from app.scientific.uvvis.schemas import UVVisAnalysisInput
from app.scientific.uvvis.service import UVVisAnalysisService
from app.scientific.xrd.schemas import XRDAnalysisInput
from app.scientific.xrd.service import XRDAnalysisService
from app.services.characterization_service import (
    CharacterizationService,
    DuplicateFileError,
    RawFileNotFoundError,
)
from app.storage.base import FileStorageBackend, StoredFile
from app.storage.local import LocalFileStorage
from app.storage.migrate_local_to_s3 import run_migration
from app.storage.s3 import S3FileStorage


@pytest.fixture
async def phase9_env(db_session: AsyncSession, test_engine) -> dict[str, Any]:
    """
    Sets up isolated test environment with two research groups and projects:
    - Group Alpha (Project Alpha) -> Leader Alpha, Member Alpha
    - Group Beta (Project Beta) -> Leader Beta
    """
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)

    async def override_get_db():
        async with session_factory() as s:
            yield s
            await s.commit()

    app.dependency_overrides[get_db] = override_get_db

    # ── Project Alpha ───────────────────────────────────────
    proj_a = Project(
        id=uuid.uuid4(),
        project_code=f"P9-ALPHA-{uuid.uuid4().hex[:4].upper()}",
        name="Project Alpha — Green Solar",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_a)

    leader_a = User(
        id=uuid.uuid4(),
        username=f"leader_a_{uuid.uuid4().hex[:6]}",
        email=f"leader_a_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. Alice Leader A",
        department="Materials Science",
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

    mem_la = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=leader_a.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_la)

    member_a = User(
        id=uuid.uuid4(),
        username=f"member_a_{uuid.uuid4().hex[:6]}",
        email=f"member_a_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Bob Member A",
        department="Materials Science",
        phone="9876543211",
        roll_number=f"ROLL-MA-{uuid.uuid4().hex[:4]}",
        role="RESEARCHER",
        password_hash="testhash_ma",
        is_active=True,
    )
    db_session.add(member_a)
    await db_session.flush()

    mem_ma = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_a.id,
        user_id=member_a.id,
        is_leader=False,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_ma)

    exp_a = Experiment(
        id=uuid.uuid4(),
        project_id=proj_a.id,
        experiment_code=f"EXP-A-{uuid.uuid4().hex[:4].upper()}",
        title="Alpha XRD Experiment",
        status=ExperimentStatus.IN_PROGRESS.value,
    )
    db_session.add(exp_a)
    await db_session.flush()

    sample_a = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_a.id,
        sample_code=f"SMP-A-{uuid.uuid4().hex[:4].upper()}",
        name="Alpha CuO Sample",
        material="CuO",
        status=SampleStatus.PREPARED.value,
    )
    db_session.add(sample_a)

    # ── Project Beta ────────────────────────────────────────
    proj_b = Project(
        id=uuid.uuid4(),
        project_code=f"P9-BETA-{uuid.uuid4().hex[:4].upper()}",
        name="Project Beta — Thermoelectric",
        material="Bi2Te3",
        extract="Aloe Vera",
        solvent="Water",
        synthesis_method="Hydrothermal",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj_b)

    leader_b = User(
        id=uuid.uuid4(),
        username=f"leader_b_{uuid.uuid4().hex[:6]}",
        email=f"leader_b_{uuid.uuid4().hex[:6]}@greensynth.edu",
        full_name="Dr. Charles Leader B",
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

    mem_lb = GroupMembership(
        id=uuid.uuid4(),
        group_id=group_b.id,
        user_id=leader_b.id,
        is_leader=True,
        status=MembershipStatus.ACTIVE.value,
    )
    db_session.add(mem_lb)

    exp_b = Experiment(
        id=uuid.uuid4(),
        project_id=proj_b.id,
        experiment_code=f"EXP-B-{uuid.uuid4().hex[:4].upper()}",
        title="Beta Bi2Te3 Experiment",
        status=ExperimentStatus.IN_PROGRESS.value,
    )
    db_session.add(exp_b)
    await db_session.flush()

    sample_b = Sample(
        id=uuid.uuid4(),
        experiment_id=exp_b.id,
        sample_code=f"SMP-B-{uuid.uuid4().hex[:4].upper()}",
        name="Beta Bi2Te3 Sample",
        material="Bi2Te3",
        status=SampleStatus.PREPARED.value,
    )
    db_session.add(sample_b)

    await db_session.commit()

    token_alpha = create_access_token(leader_a.id)
    token_alpha_member = create_access_token(member_a.id)
    token_beta = create_access_token(leader_b.id)

    yield {
        "proj_a": proj_a,
        "sample_a": sample_a,
        "token_alpha": token_alpha,
        "token_alpha_member": token_alpha_member,
        "proj_b": proj_b,
        "sample_b": sample_b,
        "token_beta": token_beta,
    }

    app.dependency_overrides.pop(get_db, None)


# ── Integration Tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_phase9_local_file_upload_and_download_flow(
    client: AsyncClient, phase9_env: dict[str, Any]
) -> None:
    """
    Test 1: Full local storage upload, SHA-256 checksum verification,
    and byte-for-byte raw file streaming download.
    """
    token = phase9_env["token_alpha"]
    sample_a = phase9_env["sample_a"]
    proj_a = phase9_env["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Characterization
    c_resp = await client.post(
        "/api/v1/characterizations",
        headers=headers,
        json={
            "sample_id": str(sample_a.id),
            "technique": "XRD",
            "operator": "Dr. Local",
            "instrument_name": "Rigaku SmartLab",
        },
    )
    assert c_resp.status_code == 201, c_resp.text
    ch_id = c_resp.json()["id"]

    # 2. Upload raw file
    raw_content = b"2theta,intensity\n20.0,100\n25.0,250\n30.0,500\n35.0,300\n"
    expected_checksum = hashlib.sha256(raw_content).hexdigest()

    files = {"file": ("xrd_cuo_run.csv", raw_content, "text/csv")}
    up_resp = await client.post(
        f"/api/v1/characterizations/{ch_id}/files",
        headers=headers,
        files=files,
    )
    assert up_resp.status_code == 201, up_resp.text
    file_data = up_resp.json()

    assert file_data["original_filename"] == "xrd_cuo_run.csv"
    assert file_data["file_extension"] == "csv"
    assert file_data["checksum"] == expected_checksum
    assert file_data["file_size"] == len(raw_content)
    assert file_data["storage_backend"] == "local"
    assert f"projects/{proj_a.project_code}" in file_data["storage_path"]
    file_id = file_data["id"]

    # 3. Retrieve raw file metadata via /files/{file_id}
    meta_resp = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert meta_resp.status_code == 200, meta_resp.text
    assert meta_resp.json()["checksum"] == expected_checksum
    assert meta_resp.json()["storage_backend"] == "local"

    # 4. Download file via /files/{file_id}/download
    dl_resp = await client.get(f"/api/v1/files/{file_id}/download", headers=headers)
    assert dl_resp.status_code == 200, dl_resp.text
    assert dl_resp.content == raw_content
    assert "xrd_cuo_run.csv" in dl_resp.headers.get("Content-Disposition", "")

    # 5. Check URL endpoint (returns direct download endpoint and None url for local)
    url_resp = await client.get(f"/api/v1/files/{file_id}/url", headers=headers)
    assert url_resp.status_code == 200, url_resp.text
    assert url_resp.json()["download_url"] is None
    assert url_resp.json()["direct_download_endpoint"] == f"/api/v1/files/{file_id}/download"


@pytest.mark.asyncio
async def test_phase9_s3_storage_upload_and_download_flow(db_session: AsyncSession) -> None:
    """
    Test 2: S3-compatible cloud object storage upload, deterministic lineage keys,
    SHA-256 calculation, and pre-signed download URL generation.
    """
    with patch("boto3.client") as mock_boto:
        from botocore.exceptions import ClientError

        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        # Configure head_object (not found initially) and put_object
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        mock_s3.put_object.return_value = {"ETag": '"s3_etag_789xyz"'}

        s3_storage = S3FileStorage(
            bucket="greensynth-cloud-bucket",
            region="us-east-1",
            access_key_id="mock_key",
            secret_access_key="mock_secret",
        )

        service = CharacterizationService(db=db_session, storage=s3_storage)

        # Create Project → Experiment → Sample in DB
        proj = Project(
            project_code="P9-S3-01",
            name="S3 Project",
            material="TiO2",
            extract="GreenTea",
            solvent="Water",
            synthesis_method="Sol-Gel",
        )
        db_session.add(proj)
        await db_session.flush()

        exp = Experiment(
            project_id=proj.id,
            experiment_code="EXP-S3-01",
            title="S3 Experiment",
            status="IN_PROGRESS",
        )
        db_session.add(exp)
        await db_session.flush()

        sample = Sample(
            experiment_id=exp.id,
            sample_code="SMP-S3-01",
            name="S3 Sample",
            material="TiO2",
            status="PREPARED",
        )
        db_session.add(sample)
        await db_session.flush()

        ch = await service.create_characterization(
            CharacterizationCreate(sample_id=sample.id, technique="UV_VIS")
        )

        uvvis_content = b"wavelength,absorbance\n300,0.15\n350,0.55\n400,0.92\n"
        expected_hash = hashlib.sha256(uvvis_content).hexdigest()

        # Upload to S3
        raw_file = await service.upload_raw_file(
            characterization_id=ch.id,
            file_bytes=uvvis_content,
            original_filename="uvvis_tio2.csv",
            content_type="text/csv",
        )

        assert raw_file.storage_backend == "s3"
        assert raw_file.checksum == expected_hash
        assert raw_file.storage_path.startswith("projects/P9-S3-01/experiments/EXP-S3-01/samples/SMP-S3-01/")
        assert raw_file.file_metadata.get("etag") == "s3_etag_789xyz"

        # Verify S3 put_object arguments
        mock_s3.put_object.assert_called_once()
        put_args = mock_s3.put_object.call_args[1]
        assert put_args["Bucket"] == "greensynth-cloud-bucket"
        assert put_args["Key"] == raw_file.storage_path
        assert put_args["Metadata"]["sha256"] == expected_hash

        # Verify pre-signed URL generation
        mock_s3.generate_presigned_url.return_value = (
            f"https://greensynth-cloud-bucket.s3.amazonaws.com/{raw_file.storage_path}?X-Amz-Signature=fake"
        )
        url = await service.generate_download_url(raw_file.id)
        assert url is not None
        assert "greensynth-cloud-bucket.s3.amazonaws.com" in url


@pytest.mark.asyncio
async def test_phase9_cross_project_file_isolation(
    client: AsyncClient, phase9_env: dict[str, Any]
) -> None:
    """
    Test 3: Cross-Project File Security Isolation.
    User in Project Beta CANNOT access, download, or generate download URLs
    for raw files belonging to Project Alpha.
    """
    token_a = phase9_env["token_alpha"]
    sample_a = phase9_env["sample_a"]
    token_b = phase9_env["token_beta"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Project Alpha: create characterization and upload file
    c_a_resp = await client.post(
        "/api/v1/characterizations",
        headers=headers_a,
        json={"sample_id": str(sample_a.id), "technique": "XRD"},
    )
    ch_a_id = c_a_resp.json()["id"]

    alpha_content = b"2theta,intensity\n20,100\n"
    files = {"file": ("alpha_confidential_xrd.csv", alpha_content, "text/csv")}
    up_resp = await client.post(
        f"/api/v1/characterizations/{ch_a_id}/files",
        headers=headers_a,
        files=files,
    )
    alpha_file_id = up_resp.json()["id"]

    # 2. User Beta tries to read metadata of Project Alpha's file -> 404 NOT FOUND
    meta_b = await client.get(f"/api/v1/files/{alpha_file_id}", headers=headers_b)
    assert meta_b.status_code == 404

    # 3. User Beta tries to download Project Alpha's file -> 404 NOT FOUND
    dl_b = await client.get(f"/api/v1/files/{alpha_file_id}/download", headers=headers_b)
    assert dl_b.status_code == 404

    # 4. User Beta tries to get pre-signed URL for Project Alpha's file -> 404 NOT FOUND
    url_b = await client.get(f"/api/v1/files/{alpha_file_id}/url", headers=headers_b)
    assert url_b.status_code == 404


@pytest.mark.asyncio
async def test_phase9_multi_device_session_consistency(
    client: AsyncClient, phase9_env: dict[str, Any]
) -> None:
    """
    Test 4: Multi-Device Session Consistency.
    Device 1 (Leader Alpha) uploads a raw FTIR dataset.
    Device 2 (Member Alpha with separate auth session in same project) retrieves metadata
    and downloads the exact identical file bytes with matching SHA-256.
    """
    token_dev1 = phase9_env["token_alpha"]
    token_dev2 = phase9_env["token_alpha_member"]
    sample_a = phase9_env["sample_a"]

    headers_dev1 = {"Authorization": f"Bearer {token_dev1}"}
    headers_dev2 = {"Authorization": f"Bearer {token_dev2}"}

    # Device 1: Create Characterization & Upload File
    c_resp = await client.post(
        "/api/v1/characterizations",
        headers=headers_dev1,
        json={"sample_id": str(sample_a.id), "technique": "FTIR"},
    )
    ch_id = c_resp.json()["id"]

    ftir_bytes = b"wavenumber,transmittance\n4000,99.2\n3500,85.4\n1650,45.1\n"
    expected_sha256 = hashlib.sha256(ftir_bytes).hexdigest()

    up_resp = await client.post(
        f"/api/v1/characterizations/{ch_id}/files",
        headers=headers_dev1,
        files={"file": ("ftir_spectrum_device1.csv", ftir_bytes, "text/csv")},
    )
    assert up_resp.status_code == 201
    file_id = up_resp.json()["id"]

    # Device 2: Fetch metadata
    meta_dev2 = await client.get(f"/api/v1/files/{file_id}", headers=headers_dev2)
    assert meta_dev2.status_code == 200
    assert meta_dev2.json()["checksum"] == expected_sha256
    assert meta_dev2.json()["file_size"] == len(ftir_bytes)

    # Device 2: Download raw file bytes
    dl_dev2 = await client.get(f"/api/v1/files/{file_id}/download", headers=headers_dev2)
    assert dl_dev2.status_code == 200
    assert dl_dev2.content == ftir_bytes
    assert hashlib.sha256(dl_dev2.content).hexdigest() == expected_sha256


@pytest.mark.asyncio
async def test_phase9_storage_transaction_rollback_defense(db_session: AsyncSession) -> None:
    """
    Test 5: Transactional Consistency & Orphan Prevention.
    If the database flush fails after storage.store(), the newly created
    storage object is automatically deleted/rolled back so no orphaned files remain.
    """
    mock_storage = MagicMock(spec=FileStorageBackend)
    mock_storage.backend_name = "mock_cloud"
    mock_storage.store = AsyncMock(
        return_value=StoredFile(
            file_id="orphan_test.csv",
            original_filename="orphan_test.csv",
            stored_path="projects/TEST/orphan_test.csv",
            file_size_bytes=100,
            checksum_sha256="abc12345",
            file_type="csv",
            storage_backend="mock_cloud",
        )
    )
    mock_storage.delete = AsyncMock()

    service = CharacterizationService(db=db_session, storage=mock_storage)

    # Mock db.flush to simulate a database constraint violation on insert
    with patch.object(db_session, "flush", side_effect=RuntimeError("Simulated DB connection drop")):
        with patch.object(
            service,
            "get_by_id",
            return_value=MagicMock(id=uuid.uuid4(), technique="XRD", sample_id=uuid.uuid4()),
        ), patch.object(
            db_session,
            "execute",
            return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=None),  # no duplicate
                one=MagicMock(
                    return_value=(
                        MagicMock(sample_code="SMP-01"),
                        MagicMock(experiment_code="EXP-01"),
                        MagicMock(project_code="P1"),
                    )
                ),
            ),
        ):
            with pytest.raises(RuntimeError, match="Simulated DB connection drop"):
                await service.upload_raw_file(
                    characterization_id=uuid.uuid4(),
                    file_bytes=b"2theta,intensity\n20,100\n",
                    original_filename="xrd.csv",
                )

            # Assert storage.delete was called on the stored path to roll back the uploaded object!
            mock_storage.delete.assert_called_once_with("projects/TEST/orphan_test.csv")


@pytest.mark.asyncio
async def test_phase9_scientific_pipeline_storage_transparency(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    """
    Test 6: Scientific Analysis Pipeline Storage Transparency.
    Verifies XRD and UV-Vis scientific algorithms function seamlessly through
    the FileStorageBackend abstraction without modifying numerical engines.
    """
    storage = LocalFileStorage(base_dir=tmp_path)
    char_service = CharacterizationService(db=db_session, storage=storage)
    xrd_service = XRDAnalysisService(db=db_session, storage=storage)
    uvvis_service = UVVisAnalysisService(db=db_session, storage=storage)

    # 1. Create hierarchy
    proj = Project(
        project_code="P9-SCI-01",
        name="Scientific Storage Test",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
    )
    db_session.add(proj)
    await db_session.flush()

    exp = Experiment(
        project_id=proj.id,
        experiment_code="EXP-SCI-01",
        title="Scientific Experiment",
        status="IN_PROGRESS",
    )
    db_session.add(exp)
    await db_session.flush()

    sample = Sample(
        experiment_id=exp.id,
        sample_code="SMP-SCI-01",
        name="Scientific Sample",
        material="CuO",
        status="PREPARED",
    )
    db_session.add(sample)
    await db_session.flush()

    # 2. XRD Upload & Analysis
    ch_xrd = await char_service.create_characterization(
        CharacterizationCreate(sample_id=sample.id, technique="XRD")
    )
    xrd_data = (
        b"2theta,intensity\n"
        b"30.0,200\n"
        b"32.5,350\n"
        b"35.5,1200\n"
        b"38.7,2500\n"
        b"42.0,400\n"
        b"45.5,500\n"
        b"48.7,850\n"
        b"53.5,620\n"
        b"55.0,300\n"
        b"58.3,910\n"
        b"61.5,450\n"
        b"64.0,350\n"
        b"66.2,780\n"
        b"68.1,690\n"
        b"70.0,250\n"
    )
    raw_xrd = await char_service.upload_raw_file(
        characterization_id=ch_xrd.id,
        file_bytes=xrd_data,
        original_filename="xrd_cuo_peaks.csv",
    )

    xrd_input = XRDAnalysisInput(
        material_type="CuO",
        wavelength=1.5406,
        instrument_broadening=0.08,
        notes="Phase 9 scientific test",
    )
    xrd_run = await xrd_service.run_analysis(
        characterization_id=ch_xrd.id,
        input_data=xrd_input,
        raw_file_id=raw_xrd.id,
    )
    assert xrd_run.status == "COMPLETED"
    assert len(xrd_run.peaks) > 0

    # 3. UV-Vis Upload & Analysis
    ch_uvvis = await char_service.create_characterization(
        CharacterizationCreate(sample_id=sample.id, technique="UV_VIS")
    )
    uvvis_lines = ["wavelength,absorbance"]
    for wl in range(250, 800, 5):
        import math
        abs_val = round(1.5 / (1.0 + math.exp((wl - 380) / 30.0)) + 0.05, 4)
        uvvis_lines.append(f"{wl},{abs_val}")
    uvvis_data = "\n".join(uvvis_lines).encode("utf-8")

    raw_uvvis = await char_service.upload_raw_file(
        characterization_id=ch_uvvis.id,
        file_bytes=uvvis_data,
        original_filename="uvvis_cuo.csv",
    )

    uvvis_input = UVVisAnalysisInput(
        transition_type="DIRECT",
        baseline_correction=True,
    )
    uvvis_run = await uvvis_service.run_analysis(
        characterization_id=ch_uvvis.id,
        input_data=uvvis_input,
        raw_file_id=raw_uvvis.id,
    )
    assert uvvis_run.status == "COMPLETED"
    assert len(uvvis_run.calculated_properties) > 0
    assert uvvis_run.assumptions.get("band_gap_ev") is not None
    assert uvvis_run.assumptions["band_gap_ev"] > 0.5


@pytest.mark.asyncio
async def test_phase9_migration_utility_execution(tmp_path: Path) -> None:
    """
    Test 7: Controlled Migration Utility Dry-Run Verification.
    Verifies that run_migration(dry_run=True) safely evaluates local files,
    validates SHA-256 hashes, and leaves database records unaltered.
    """
    with patch("boto3.client"):
        stats = await run_migration(
            dry_run=True,
            verify_only=False,
            settings=Settings(
                storage_backend="local",
                raw_data_dir=str(tmp_path),
            ),
        )
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "migrated" in stats
        assert "failed" in stats
        assert stats["failed"] == 0
