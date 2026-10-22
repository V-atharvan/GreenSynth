"""
GreenSynth Analytics — Processed File Path Resolver Utility

Resolves processed file paths robustly across project directory structures,
relative directory variations (backend/data vs data), and sample code formatting.
"""

from __future__ import annotations

import os
from pathlib import Path
from app.core.config import get_settings, _PROJECT_ROOT

def resolve_processed_file_path(stored_path: str) -> Path | None:
    """
    Attempt to locate a processed CSV file across known directory roots
    and path formatting variations.
    """
    settings = get_settings()
    clean_rel = os.path.normpath(stored_path).lstrip("/\\")

    configured_root = Path(getattr(settings, "processed_data_dir", "data/processed")).resolve()
    candidate_bases = [
        configured_root,
        (_PROJECT_ROOT / "data" / "processed").resolve(),
        (_PROJECT_ROOT / "backend" / "data" / "processed").resolve(),
        Path("data/processed").resolve(),
        Path("backend/data/processed").resolve(),
    ]

    candidate_rels = {
        clean_rel,
        clean_rel.replace("projects/", "", 1) if clean_rel.startswith("projects/") else "projects/" + clean_rel,
        clean_rel.replace("P7 S1", "P7S1"),
        clean_rel.replace("P7S1", "P7 S1"),
    }

    for base in candidate_bases:
        if not base.exists():
            continue
        for rel in candidate_rels:
            cand = (base / rel).resolve()
            if cand.exists() and cand.is_file() and cand.stat().st_size > 10:
                return cand

    return None
