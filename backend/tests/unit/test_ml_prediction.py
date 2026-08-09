"""
GreenSynth Analytics — Unit Tests: ML Applicability & Uncertainty
"""

from __future__ import annotations

import pytest

from app.ml.prediction.applicability import ApplicabilityChecker
from app.ml.prediction.uncertainty import UncertaintyEstimator


def test_applicability_checker():
    checker = ApplicabilityChecker()
    training_ranges = {
        "substrate_temperature": {"min": 250.0, "max": 400.0},
        "spray_rate": {"min": 1.0, "max": 5.0},
    }

    # In domain input
    res1 = checker.check_applicability(
        input_values={"substrate_temperature": 320.0, "spray_rate": 3.0},
        training_feature_ranges=training_ranges,
    )
    assert res1.status == "VALID"
    assert res1.is_in_domain is True

    # Out of domain input (e.g. 550°C)
    res2 = checker.check_applicability(
        input_values={"substrate_temperature": 550.0, "spray_rate": 3.0},
        training_feature_ranges=training_ranges,
    )
    assert res2.status == "OUT_OF_DOMAIN"
    assert res2.is_in_domain is False
    assert len(res2.warnings) > 0


def test_uncertainty_estimator():
    estimator = UncertaintyEstimator()

    res = estimator.estimate_uncertainty(
        predicted_value=12.5,
        validation_rmse=0.5,
        confidence_factor=1.96,
    )

    assert res.predicted_value == 12.5
    assert res.uncertainty_lower < 12.5
    assert res.uncertainty_upper > 12.5
    assert res.uncertainty_margin == round(1.96 * 0.5, 4)
