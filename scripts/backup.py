"""
GreenSynth Analytics — Backup Maintenance Utility (Phase 20)

Creates a complete timestamped backup ZIP archive containing:
  1. SQLite Database (greensynth.db)
  2. Raw laboratory files directory
  3. Manifest file (manifest.json) with cryptographic SHA-256 checksums
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def calculate_sha256(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_backup(
    db_path: str = "greensynth.db",
    storage_dir: str = "uploads",
    backup_dir: str = "backups",
) -> Path:
    base_dir = Path.cwd()
    backup_folder = base_dir / backup_dir
    backup_folder.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"greensynth_backup_{timestamp}.zip"
    backup_filepath = backup_folder / backup_filename

    manifest: dict = {
        "timestamp": now_utc.isoformat(),
        "platform_version": "1.0.0-research",
        "files": {},
    }

    print(f"[BACKUP] Creating backup archive: {backup_filepath.name}...")

    with zipfile.ZipFile(backup_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Backup SQLite DB
        db_file = base_dir / db_path
        if db_file.exists():
            arc_name = "database/greensynth.db"
            zipf.write(db_file, arc_name)
            checksum = calculate_sha256(db_file)
            manifest["files"][arc_name] = {
                "size_bytes": db_file.stat().st_size,
                "sha256": checksum,
            }
            print(f"  [DB] Archived database: {db_path} ({db_file.stat().st_size} bytes)")
        else:
            print(f"  [WARN] Database file '{db_path}' not found!")

        # 2. Backup storage directory
        store_folder = base_dir / storage_dir
        if store_folder.exists():
            for root, _, files in os.walk(store_folder):
                for f in files:
                    fp = Path(root) / f
                    rel_p = fp.relative_to(base_dir)
                    arc_name = str(rel_p).replace("\\", "/")
                    zipf.write(fp, arc_name)
                    checksum = calculate_sha256(fp)
                    manifest["files"][arc_name] = {
                        "size_bytes": fp.stat().st_size,
                        "sha256": checksum,
                    }
            print(f"  [STORAGE] Archived storage directory: {storage_dir}")
        else:
            print(f"  [INFO] Storage directory '{storage_dir}' is empty or uncreated.")

        # 3. Save Manifest JSON inside zip
        manifest_data = json.dumps(manifest, indent=2)
        zipf.writestr("manifest.json", manifest_data)
        print("  [MANIFEST] Generated manifest.json with cryptographic SHA-256 hashes.")

    print(f"[SUCCESS] Backup complete! Archive saved to: {backup_filepath}")
    return backup_filepath


if __name__ == "__main__":
    create_backup()
