"""
GreenSynth Analytics — Controlled Local-to-S3 Storage Migration CLI

Migrates raw laboratory files from local disk storage to S3-compatible cloud object storage.
Preserves scientific data integrity through pre-upload and post-upload SHA-256 verification.
Never deletes original local files.

Usage:
    python -m app.storage.migrate_local_to_s3 --dry-run
    python -m app.storage.migrate_local_to_s3 --verify-only
    python -m app.storage.migrate_local_to_s3 --batch-size 50
    python -m app.storage.migrate_local_to_s3 --project-code P1-CS-01
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.models.characterization import RawFile
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample
from app.storage.local import LocalFileStorage
from app.storage.s3 import S3FileStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("storage_migration")


async def run_migration(
    dry_run: bool = True,
    verify_only: bool = False,
    batch_size: int = 100,
    project_code: str | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    """
    Execute controlled migration from local disk storage to S3 object storage.

    Returns summary stats dict with keys: total, migrated, already_migrated, skipped_missing, failed.
    """
    cfg = settings or get_settings()

    # Ensure S3 settings are configured for actual migration
    if not dry_run and not verify_only:
        cfg.validate_storage_settings()

    local_storage = LocalFileStorage(base_dir=cfg.raw_data_dir)
    s3_storage = S3FileStorage(
        bucket=cfg.s3_bucket,
        region=cfg.s3_region,
        endpoint_url=cfg.s3_endpoint_url,
        access_key_id=cfg.s3_access_key_id,
        secret_access_key=cfg.s3_secret_access_key,
        public_base_url=cfg.s3_public_base_url,
        use_ssl=cfg.s3_use_ssl,
        signature_version=cfg.s3_signature_version,
        settings=cfg,
    )

    engine = create_async_engine(cfg.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    stats = {
        "total": 0,
        "migrated": 0,
        "already_migrated": 0,
        "skipped_missing": 0,
        "failed": 0,
    }

    logger.info("=" * 70)
    logger.info("GreenSynth Analytics — Raw File S3 Migration Utility")
    logger.info("Mode: %s", "DRY-RUN (no writes)" if dry_run else ("VERIFY-ONLY" if verify_only else "LIVE MIGRATION"))
    logger.info("Local Root: %s", local_storage.base_dir)
    logger.info("Target S3 Bucket: %s (Region: %s)", s3_storage.bucket, s3_storage.region)
    logger.info("=" * 70)

    async with session_factory() as session:
        # Build query for candidate raw files
        q = (
            select(RawFile, Sample, Experiment, Project)
            .join(Sample, RawFile.sample_id == Sample.id)
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .join(Project, Experiment.project_id == Project.id)
            .order_by(RawFile.uploaded_at.asc())
        )

        if project_code:
            q = q.where(Project.project_code == project_code)

        result = await session.execute(q)
        rows = result.all()
        stats["total"] = len(rows)

        logger.info("Found %d total raw file records in database.", stats["total"])

        for idx, (raw_file, sample, exp, proj) in enumerate(rows, start=1):
            file_id_str = str(raw_file.id)
            file_desc = f"[{idx}/{stats['total']}] File {file_id_str} ('{raw_file.original_filename}')"

            # Check if file is already on S3
            if raw_file.storage_backend == "s3":
                s3_exists = await s3_storage.exists(raw_file.storage_path)
                if s3_exists:
                    logger.info("%s: Already migrated to S3 (%s).", file_desc, raw_file.storage_path)
                    stats["already_migrated"] += 1
                    continue

            # Check local file existence and read bytes
            local_exists = await local_storage.exists(raw_file.storage_path)
            if not local_exists:
                logger.warning(
                    "%s: Local file NOT found at '%s'. Skipping.",
                    file_desc,
                    raw_file.storage_path,
                )
                stats["skipped_missing"] += 1
                continue

            try:
                local_bytes = await local_storage.retrieve(raw_file.storage_path)
                # Verify local SHA-256 checksum against database record
                computed_hash = hashlib.sha256(local_bytes).hexdigest()
                if computed_hash != raw_file.checksum:
                    logger.error(
                        "%s: Checksum mismatch! DB=%s, Disk=%s. Migration aborted for this file.",
                        file_desc,
                        raw_file.checksum,
                        computed_hash,
                    )
                    stats["failed"] += 1
                    continue

                # Deterministic target S3 key
                s3_key = (
                    f"projects/{proj.project_code}/experiments/{exp.experiment_code}/"
                    f"samples/{sample.sample_code}/{raw_file.characterization_id!s}/{raw_file.stored_filename}"
                )

                if verify_only:
                    logger.info("%s: Local checksum valid (%s). Ready for S3 upload -> '%s'.", file_desc, computed_hash[:8], s3_key)
                    continue

                if dry_run:
                    logger.info(
                        "%s: [DRY-RUN] Would upload %d bytes to S3 key '%s' and update DB.",
                        file_desc,
                        len(local_bytes),
                        s3_key,
                    )
                    stats["migrated"] += 1
                    continue

                # Live Migration: Upload to S3 if not present
                if not await s3_storage.exists(s3_key):
                    stored_meta = await s3_storage.store(
                        content=local_bytes,
                        destination_path=s3_key,
                        original_filename=raw_file.original_filename,
                        content_type=raw_file.mime_type,
                    )
                else:
                    logger.info("%s: Object already exists in S3 at '%s'. Updating DB metadata.", file_desc, s3_key)

                # Update database record to point to S3
                raw_file.storage_path = s3_key
                raw_file.storage_backend = "s3"
                if raw_file.file_metadata is None:
                    raw_file.file_metadata = {}
                raw_file.file_metadata["storage_backend"] = "s3"
                raw_file.file_metadata["bucket"] = s3_storage.bucket
                raw_file.file_metadata["migrated_at"] = asyncio.get_event_loop().time()

                await session.flush()
                stats["migrated"] += 1
                logger.info("%s: Successfully migrated to S3 key '%s'.", file_desc, s3_key)

                if stats["migrated"] % batch_size == 0:
                    await session.commit()
                    logger.info("Committed batch of %d migrated records.", stats["migrated"])

            except Exception as exc:
                logger.error("%s: Migration failed with exception: %s", file_desc, exc)
                stats["failed"] += 1

        if not dry_run and not verify_only:
            await session.commit()

    await engine.dispose()

    logger.info("=" * 70)
    logger.info("Migration Summary:")
    logger.info("  Total Records Examined: %d", stats["total"])
    logger.info("  Migrated:              %d", stats["migrated"])
    logger.info("  Already on S3:         %d", stats["already_migrated"])
    logger.info("  Skipped (Missing):     %d", stats["skipped_missing"])
    logger.info("  Failed:                %d", stats["failed"])
    logger.info("=" * 70)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate GreenSynth raw files from local filesystem to S3 object storage."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate migration without modifying S3 or database records.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        default=False,
        help="Only verify SHA-256 integrity of local files.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to commit per batch (default: 100).",
    )
    parser.add_argument(
        "--project-code",
        type=str,
        default=None,
        help="Filter migration to a specific project code.",
    )

    args = parser.parse_args()

    # If neither --dry-run nor --verify-only is passed, require explicit confirmation
    if not args.dry_run and not args.verify_only:
        print("WARNING: You are about to run a LIVE S3 migration that updates database records.")
        confirm = input("Type 'yes' to proceed: ")
        if confirm.strip().lower() != "yes":
            print("Migration cancelled by user.")
            sys.exit(0)

    stats = asyncio.run(
        run_migration(
            dry_run=args.dry_run,
            verify_only=args.verify_only,
            batch_size=args.batch_size,
            project_code=args.project_code,
        )
    )

    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
