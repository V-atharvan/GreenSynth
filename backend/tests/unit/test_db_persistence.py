"""
Unit tests for Database Persistence, Engine Configuration, and URL Normalization (Phase 26 Persistence Fix)
"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.project import Project, ProjectStatus
from app.models.experiment import Experiment, ExperimentStatus
from app.models.sample import Sample, SampleStatus
from app.models.characterization import Characterization, TechniqueType, CharacterizationStatus, RawFile, RawFileStatus
from app.models.analysis import AnalysisRun, AnalysisStatus, CalculatedProperty
from app.models.ml import MLDataset, MLDatasetRecord
from app.core.method_config import get_allowed_parameter_codes, validate_parameters_for_project


def test_database_url_normalization():
    """Verify that postgres:// and postgresql:// URLs are normalized to asyncpg for async and psycopg2 for sync."""
    s = Settings(
        database_url="postgres://user:pass@ep-cool-host.neon.tech/greensynth?sslmode=require",
        database_url_sync="postgres://user:pass@ep-cool-host.neon.tech/greensynth?sslmode=require",
    )
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert "user:pass@ep-cool-host.neon.tech" in s.database_url
    assert s.database_url_sync.startswith("postgresql+psycopg2://")

    # Standard postgresql:// URL
    s2 = Settings(
        database_url="postgresql://user:pass@render-pg.com:5432/greensynth_prod",
        database_url_sync="postgresql://user:pass@render-pg.com:5432/greensynth_prod",
    )
    assert s2.database_url.startswith("postgresql+asyncpg://")
    assert s2.database_url_sync.startswith("postgresql+psycopg2://")

    # SQLite URL normalization
    s3 = Settings(
        database_url="sqlite:///app/greensynth.db",
    )
    assert s3.database_url.startswith("sqlite+aiosqlite://")


@pytest.mark.asyncio
async def test_experiment_crud_persistence(db_session: AsyncSession):
    """Verify complete CRUD lifecycle persistence within AsyncSession."""
    # 1. Create Project
    proj = Project(
        project_code=f"P7-TEST-{uuid.uuid4().hex[:6].upper()}",
        name="Test Persistence Project",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.flush()

    # 2. Create Experiment (Create)
    exp = Experiment(
        project_id=proj.id,
        experiment_code="EXP-PERSIST-001",
        title="Persistence Verification Run",
        status=ExperimentStatus.PLANNED.value,
        researcher="QA Suite",
    )
    db_session.add(exp)
    await db_session.flush()
    exp_id = exp.id

    # 3. Read Experiment (Read)
    res = await db_session.execute(select(Experiment).where(Experiment.id == exp_id))
    fetched_exp = res.scalar_one()
    assert fetched_exp is not None
    assert fetched_exp.experiment_code == "EXP-PERSIST-001"
    assert fetched_exp.status == ExperimentStatus.PLANNED.value

    # 4. Update Experiment (Update)
    fetched_exp.status = ExperimentStatus.COMPLETED.value
    fetched_exp.notes = "Completed and persisted to database."
    await db_session.flush()

    res_updated = await db_session.execute(select(Experiment).where(Experiment.id == exp_id))
    updated_exp = res_updated.scalar_one()
    assert updated_exp.status == ExperimentStatus.COMPLETED.value
    assert "Completed and persisted" in updated_exp.notes

    # 5. Delete Experiment (Delete)
    await db_session.delete(updated_exp)
    await db_session.flush()

    res_deleted = await db_session.execute(select(Experiment).where(Experiment.id == exp_id))
    assert res_deleted.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cross_entity_relationship_persistence(db_session: AsyncSession):
    """Verify full entity relationship tree persists correctly across foreign keys."""
    # Project
    proj = Project(
        project_code=f"P7-REL-{uuid.uuid4().hex[:6].upper()}",
        name="Relationship Integrity Project",
        material="CuO",
        synthesis_method="Spray Pyrolysis",
        solvent="ETHANOL",
        extract="Mulberry",
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    await db_session.flush()

    # Experiment
    exp = Experiment(
        project_id=proj.id,
        experiment_code="EXP-REL-001",
        title="Full Relationship Test Run",
        status=ExperimentStatus.COMPLETED.value,
        researcher="QA Lead",
    )
    db_session.add(exp)
    await db_session.flush()

    # Sample
    sample = Sample(
        experiment_id=exp.id,
        sample_code="SAMP-REL-001-A",
        name="Rel Sample A",
        status=SampleStatus.COMPLETED.value,
    )
    db_session.add(sample)
    await db_session.flush()

    # Characterization
    char = Characterization(
        sample_id=sample.id,
        technique=TechniqueType.ELECTRICAL.value,
        status=CharacterizationStatus.ANALYZED.value,
    )
    db_session.add(char)
    await db_session.flush()

    # Raw File
    raw_file = RawFile(
        characterization_id=char.id,
        sample_id=sample.id,
        original_filename="iv_curve_001.csv",
        stored_filename="iv_measurement.csv",
        file_extension="csv",
        file_size=1024,
        checksum="a" * 64,
        mime_type="text/csv",
        storage_path="uploads/test.csv",
        status=RawFileStatus.ACTIVE.value,
    )
    db_session.add(raw_file)
    await db_session.flush()

    # Analysis Run
    run = AnalysisRun(
        characterization_id=char.id,
        input_file_id=raw_file.id,
        analysis_type="ELECTRICAL",
        status=AnalysisStatus.COMPLETED.value,
        software_version="1.0.0",
        assumptions={"probe_spacing_cm": 0.1, "geometry": "thin_film"},
        notes="Four-point probe ohmic fit",
    )
    db_session.add(run)
    await db_session.flush()

    # Calculated Property
    prop = CalculatedProperty(
        sample_id=sample.id,
        analysis_run_id=run.id,
        property_name="Electrical Conductivity",
        value=8.5,
        unit="S/cm",
        calculation_method="Four-Point Probe Resistance Fit",
    )
    db_session.add(prop)
    await db_session.flush()

    # ML Dataset & Record
    ds = MLDataset(
        project_id=proj.id,
        name="Persistence Verification Dataset",
        target_property="Electrical Conductivity",
        target_unit="S/cm",
        features=[{"name": "substrate_temperature", "type": "numerical"}],
        eligible_count=1,
        excluded_count=0,
        status="IMMUTABLE",
    )
    db_session.add(ds)
    await db_session.flush()

    rec = MLDatasetRecord(
        dataset_id=ds.id,
        experiment_id=exp.id,
        sample_id=sample.id,
        analysis_run_id=run.id,
        feature_values={"substrate_temperature": 380.0},
        target_value=8.5,
        target_unit="S/cm",
        is_eligible=True,
    )
    db_session.add(rec)
    await db_session.flush()

    # Verify query traversal from MLDatasetRecord back to Project
    res_rec = await db_session.execute(select(MLDatasetRecord).where(MLDatasetRecord.id == rec.id))
    fetched_rec = res_rec.scalar_one()
    assert fetched_rec.target_value == 8.5
    assert fetched_rec.experiment_id == exp.id
    assert fetched_rec.sample_id == sample.id
    assert fetched_rec.analysis_run_id == run.id


def test_method_parameter_isolation_integrity():
    """Verify that project methodologies (P1 Sol-Gel, P3 Hydrothermal, P5 Silica, P7 Spray) remain strictly isolated."""
    p1_codes = get_allowed_parameter_codes("P1")
    p3_codes = get_allowed_parameter_codes("P3")
    p7_codes = get_allowed_parameter_codes("P7")

    # Sol-Gel should have aging and calcination parameters, but NO spray parameters
    assert "sol_gel_aging_temperature_c" in p1_codes
    assert "calcination_temperature_c" in p1_codes
    assert "spray_rate_ml_min" not in p1_codes
    assert "spray_duration_min" not in p1_codes
    assert "nozzle_substrate_distance_cm" not in p1_codes

    # Hydrothermal should have autoclave parameters, but NO spray parameters
    assert "autoclave_fill_factor_pct" in p3_codes
    assert "hydrothermal_temperature_c" in p3_codes
    assert "spray_rate_ml_min" not in p3_codes

    # Spray Pyrolysis should have spray parameters, but NO autoclave or sol-gel aging parameters
    assert "substrate_temperature_c" in p7_codes
    assert "spray_rate_ml_min" in p7_codes
    assert "spray_duration_min" in p7_codes
    assert "nozzle_substrate_distance_cm" in p7_codes
    assert "autoclave_fill_factor_pct" not in p7_codes
    assert "sol_gel_aging_temperature_c" not in p7_codes

    # Validation rejection for invalid parameters
    valid_p1, msg_p1 = validate_parameters_for_project("P1", {"spray_rate_ml_min": 5.0})
    assert valid_p1 is False
    assert "Sol-Gel" in msg_p1

    valid_p7, msg_p7 = validate_parameters_for_project("P7", {"substrate_temperature_c": 350.0, "spray_rate_ml_min": 5.0})
    assert valid_p7 is True
    assert msg_p7 is None
