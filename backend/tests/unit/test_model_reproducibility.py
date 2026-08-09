"""
GreenSynth Analytics — Model Reproducibility & Artifact Serialization Tests (Phase 16)
"""

import pytest
import numpy as np
from app.ml.models.random_forest import RandomForestModel
from app.ml.preprocessing.pipeline import PreprocessingPipeline
from app.ml.registry.artifact_store import ModelArtifactStore


def test_model_reproducibility_with_seed():
    """Verify model training with identical random seed produces identical predictions."""
    X = np.array([[300.0, 2.0], [350.0, 3.0], [400.0, 5.0], [350.0, 4.0]])
    y = np.array([1.2, 3.4, 5.8, 4.1])

    rf1 = RandomForestModel(hyperparameters={"n_estimators": 10, "random_state": 42})
    rf1.fit(X, y, ["temp", "rate"])

    rf2 = RandomForestModel(hyperparameters={"n_estimators": 10, "random_state": 42})
    rf2.fit(X, y, ["temp", "rate"])

    p1 = rf1.predict(X)
    p2 = rf2.predict(X)
    np.testing.assert_array_almost_equal(p1, p2)


def test_model_artifact_serialization_and_checksum(tmp_path):
    """Verify saving artifact, calculating SHA256 checksum, and reloading artifact."""
    store = ModelArtifactStore(base_dir=str(tmp_path))
    rf = RandomForestModel(hyperparameters={"n_estimators": 5, "random_state": 42})
    X = np.array([[300.0], [400.0]])
    y = np.array([1.0, 5.0])
    rf.fit(X, y, ["temp"])

    pipe = PreprocessingPipeline(scaling="STANDARD")
    pipe.fit_transform(X, ["temp"])

    art_path, sha256 = store.save_artifact(
        model_id="test-m1",
        model=rf,
        preprocessing_pipeline=pipe,
        metadata={"target": "cond"},
    )
    assert len(sha256) == 64

    # Load artifact with expected checksum
    bundle = store.load_artifact(art_path, expected_hash=sha256)
    loaded_model = bundle["model"]
    loaded_pipe = bundle["pipeline"]

    p_orig = rf.predict(pipe.transform(X))
    p_loaded = loaded_model.predict(loaded_pipe.transform(X))
    np.testing.assert_array_almost_equal(p_orig, p_loaded)
