"""
GreenSynth Analytics — Data Integrity & Storage Verification Engine (Phase 20)

Provides:
  1. verify_storage(): SHA-256 hash recalculation and physical file verification.
  2. verify_database(): Relational orphan record detection and consistency checks.
  3. generate_integrity_report(): Full research dataset & system audit report.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisRun, CalculatedProperty
from app.models.characterization import Characterization, RawFile
from app.models.experiment import Experiment
from app.models.ml import MLDataset, MLModel, MLPrediction
from app.models.optimization import OptimizationCandidate, OptimizationRun
from app.models.project import Project
from app.models.sample import Sample


class DataIntegrityService:
    """
    Data integrity auditing and verification engine.
    """

    @staticmethod
    def calculate_sha256(filepath: str | Path) -> str:
        """Calculate SHA-256 cryptographic hash of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    async def verify_storage(cls, db: AsyncSession) -> dict[str, Any]:
        """
        Scans all RawFile records in the database, recalculates SHA-256 hashes,
        and verifies physical file integrity.
        """
        stmt = select(RawFile).where(RawFile.status == "ACTIVE")
        res = await db.execute(stmt)
        raw_files = res.scalars().all()

        verified_count = 0
        missing_files: list[dict[str, Any]] = []
        checksum_mismatches: list[dict[str, Any]] = []

        for rf in raw_files:
            file_path = Path(rf.storage_path)
            if not file_path.exists():
                missing_files.append({
                    "file_id": str(rf.id),
                    "filename": rf.original_filename,
                    "storage_path": rf.storage_path,
                    "expected_checksum": rf.checksum,
                })
                continue

            current_checksum = cls.calculate_sha256(file_path)
            if current_checksum != rf.checksum:
                checksum_mismatches.append({
                    "file_id": str(rf.id),
                    "filename": rf.original_filename,
                    "stored_checksum": rf.checksum,
                    "recalculated_checksum": current_checksum,
                })
            else:
                verified_count += 1

        is_clean = len(missing_files) == 0 and len(checksum_mismatches) == 0

        return {
            "status": "HEALTHY" if is_clean else "INTEGRITY_WARNING",
            "total_files_checked": len(raw_files),
            "verified_intact_count": verified_count,
            "missing_files_count": len(missing_files),
            "checksum_mismatches_count": len(checksum_mismatches),
            "missing_files": missing_files,
            "checksum_mismatches": checksum_mismatches,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @classmethod
    async def verify_database(cls, db: AsyncSession) -> dict[str, Any]:
        """
        Performs relational checks for orphan records across the database.
        """
        warnings: list[str] = []

        # 1. Samples without experiment
        s_stmt = select(Sample).where(Sample.experiment_id.is_(None))
        s_res = await db.execute(s_stmt)
        orphan_samples = s_res.scalars().all()
        if orphan_samples:
            warnings.append(f"Found {len(orphan_samples)} sample records without an assigned experiment_id.")

        # 2. Experiments without project
        e_stmt = select(Experiment).where(Experiment.project_id.is_(None))
        e_res = await db.execute(e_stmt)
        orphan_exps = e_res.scalars().all()
        if orphan_exps:
            warnings.append(f"Found {len(orphan_exps)} experiment records without an assigned project_id.")

        # 3. Predictions without model
        p_stmt = select(MLPrediction).where(MLPrediction.model_id.is_(None))
        p_res = await db.execute(p_stmt)
        orphan_preds = p_res.scalars().all()
        if orphan_preds:
            warnings.append(f"Found {len(orphan_preds)} ML predictions without an assigned model_id.")

        is_clean = len(warnings) == 0

        return {
            "status": "HEALTHY" if is_clean else "INTEGRITY_WARNING",
            "database_integrity_warnings": warnings,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @classmethod
    async def generate_integrity_report(cls, db: AsyncSession) -> dict[str, Any]:
        """
        Generates full scientific data audit report summarizing record counts and lineage health.
        """
        p_cnt = (await db.execute(select(func.count(Project.id)))).scalar() or 0
        e_cnt = (await db.execute(select(func.count(Experiment.id)))).scalar() or 0
        s_cnt = (await db.execute(select(func.count(Sample.id)))).scalar() or 0
        f_cnt = (await db.execute(select(func.count(RawFile.id)))).scalar() or 0
        c_cnt = (await db.execute(select(func.count(Characterization.id)))).scalar() or 0
        a_cnt = (await db.execute(select(func.count(AnalysisRun.id)))).scalar() or 0
        prop_cnt = (await db.execute(select(func.count(CalculatedProperty.id)))).scalar() or 0
        ds_cnt = (await db.execute(select(func.count(MLDataset.id)))).scalar() or 0
        m_cnt = (await db.execute(select(func.count(MLModel.id)))).scalar() or 0
        pred_cnt = (await db.execute(select(func.count(MLPrediction.id)))).scalar() or 0
        opt_cnt = (await db.execute(select(func.count(OptimizationCandidate.id)))).scalar() or 0

        storage_audit = await cls.verify_storage(db)
        db_audit = await cls.verify_database(db)

        return {
            "platform_version": "1.0.0-research",
            "audit_timestamp": datetime.utcnow().isoformat(),
            "record_counts": {
                "projects": p_cnt,
                "experiments": e_cnt,
                "samples": s_cnt,
                "raw_files": f_cnt,
                "characterizations": c_cnt,
                "analysis_runs": a_cnt,
                "calculated_properties": prop_cnt,
                "datasets": ds_cnt,
                "models": m_cnt,
                "predictions": pred_cnt,
                "optimization_candidates": opt_cnt,
            },
            "storage_verification": storage_audit,
            "database_verification": db_audit,
        }
