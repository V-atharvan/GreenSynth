"""
GreenSynth Analytics — Restore Maintenance Utility (Phase 20)

Restores SQLite database and raw file storage from a backup ZIP archive,
verifying cryptographic SHA-256 manifest hashes before restoring.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def restore_backup(backup_zip_path: str | Path) -> bool:
    zip_path = Path(backup_zip_path)
    if not zip_path.exists():
        print(f"[ERROR] Backup file '{zip_path}' not found!")
        return False

    base_dir = Path.cwd()
    print(f"[RESTORE] Restoring system from backup archive: {zip_path.name}...")

    with zipfile.ZipFile(zip_path, "r") as zipf:
        if "manifest.json" not in zipf.namelist():
            print("[ERROR] Backup archive is invalid (missing manifest.json).")
            return False

        manifest_content = zipf.read("manifest.json").decode("utf-8")
        manifest = json.loads(manifest_content)

        print(f"  [MANIFEST] Timestamp: {manifest.get('timestamp')}")
        print(f"  [MANIFEST] Platform version: {manifest.get('platform_version')}")

        # Verify SHA-256 hashes
        mismatches = 0
        for arc_name, meta in manifest.get("files", {}).items():
            if arc_name in zipf.namelist():
                file_bytes = zipf.read(arc_name)
                calc_hash = calculate_sha256(file_bytes)
                if calc_hash != meta["sha256"]:
                    print(f"  [ERROR] Checksum mismatch for '{arc_name}'!")
                    mismatches += 1

        if mismatches > 0:
            print(f"[ERROR] Restore cancelled: {mismatches} file(s) failed SHA-256 verification.")
            return False

        print("  [INTEGRITY] All files passed SHA-256 verification.")

        # Perform extraction
        for member in zipf.infolist():
            if member.filename == "manifest.json":
                continue
            if member.filename.startswith("database/greensynth.db"):
                out_path = base_dir / "greensynth.db"
                out_path.write_bytes(zipf.read(member))
                print(f"  [DB] Restored database to: {out_path}")
            else:
                out_path = base_dir / member.filename
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(zipf.read(member))
                print(f"  [FILE] Restored file: {member.filename}")

    print("[SUCCESS] System successfully restored from backup!")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore.py <path_to_backup.zip>")
        sys.exit(1)
    restore_backup(sys.argv[1])
