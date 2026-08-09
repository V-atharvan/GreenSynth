"""
GreenSynth Analytics — Mandatory Data Leakage Prevention Unit Tests (Phase 16)
"""

import pytest
import numpy as np
from app.ml.preprocessing.pipeline import PreprocessingPipeline


def test_data_leakage_scaler_isolation():
    """Verify StandardScaler parameters are computed strictly on Train set only."""
    train_ids = ["s1", "s2", "s3", "s4"]
    test_ids = ["s5", "s6"]

    # Verify no sample ID overlap
    assert PreprocessingPipeline.verify_no_leakage(train_ids, test_ids) is True

    # Overlapping sample IDs must raise ValueError
    with pytest.raises(ValueError, match="Data leakage detected"):
        PreprocessingPipeline.verify_no_leakage(train_ids, ["s3", "s5"])

    # Verify Scaler scaling parameters (mean, scale) depend solely on Train set
    X_train = np.array([[300.0], [350.0], [400.0]])
    X_test = np.array([[600.0], [700.0]])

    pipe = PreprocessingPipeline(scaling="STANDARD")
    X_train_scaled = pipe.fit_transform(X_train, ["temp"])
    cfg = pipe.get_config()

    # Train mean should equal 350.0
    assert abs(cfg["mean"][0] - 350.0) < 1e-5

    # Transforming Test set must use Train mean (350.0), not recompute on Test
    X_test_scaled = pipe.transform(X_test)
    assert X_test_scaled[0][0] > 3.0
