"""
GreenSynth Analytics — Phase 20 Production Hardening & Data Integrity Unit Tests
"""

import hashlib
import tempfile
from pathlib import Path

import pytest
from app.scientific.verification.integrity import DataIntegrityService


def test_sha256_hash_calculation():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"GreenSynth Analytics Scientific Test File Data\n")
        tmp_path = Path(tmp.name)

    try:
        calculated_hash = DataIntegrityService.calculate_sha256(tmp_path)
        expected_hash = hashlib.sha256(b"GreenSynth Analytics Scientific Test File Data\n").hexdigest()
        assert calculated_hash == expected_hash
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_backup_and_restore_script_importable():
    from scripts.backup import calculate_sha256 as backup_sha
    from scripts.restore import calculate_sha256 as restore_sha

    data = b"Test binary content"
    assert backup_sha == backup_sha  # import check
    assert restore_sha(data) == hashlib.sha256(data).hexdigest()
