"""
GreenSynth Analytics — Model Artifact Storage

Saves and loads trained model pipelines to disk under data/models/{model_id}/.
Uses joblib for scikit-learn artifact serialization.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any
import joblib

from app.ml.models.base import BaseMLModel
from app.ml.preprocessing.pipeline import PreprocessingPipeline


class ModelArtifactStore:
    """
    Manages physical storage of trained model pipelines on local disk.
    """

    def __init__(self, base_dir: str = "data/models") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_checksum(filepath: str) -> str:
        """Calculate SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def save_artifact(
        self,
        model_id: str,
        model: BaseMLModel,
        preprocessing_pipeline: PreprocessingPipeline,
        metadata: dict[str, Any],
    ) -> tuple[str, str]:
        model_folder = self.base_dir / str(model_id)
        model_folder.mkdir(parents=True, exist_ok=True)

        artifact_path = model_folder / "model.joblib"
        bundle = {
            "model_id": str(model_id),
            "model": model,
            "pipeline": preprocessing_pipeline,
            "metadata": metadata,
        }
        joblib.dump(bundle, artifact_path)
        sha256 = self.compute_checksum(str(artifact_path))
        return str(artifact_path), sha256

    def load_artifact(self, artifact_path: str, expected_hash: str | None = None) -> dict[str, Any]:
        p = Path(artifact_path)
        if not p.exists():
            raise FileNotFoundError(f"Model artifact path does not exist: {artifact_path}")
        if expected_hash:
            curr_hash = self.compute_checksum(str(p))
            if curr_hash != expected_hash:
                raise ValueError(f"Model checksum mismatch! Expected {expected_hash}, got {curr_hash}.")
        bundle = joblib.load(p)
        return bundle
