"""
GreenSynth Analytics — Phase 15 Evidence & Advanced Statistics Engine Unit Tests
"""

import pytest
from app.analytics.statistics.correlation import calculate_correlation_matrix, calculate_pearson_correlation
from app.analytics.statistics.descriptive import calculate_descriptive_stats, calculate_grouped_stats
from app.analytics.statistics.effect_estimation import EffectEstimationEngine
from app.analytics.statistics.model_diagnostics import ModelDiagnosticsEngine
from app.analytics.statistics.outliers import detect_outliers_iqr_or_zscore
from app.analytics.statistics.regression import fit_regression_model
from app.evidence.data_quality_engine import DataQualityEngine
from app.evidence.evidence_engine import EvidenceEngine
from app.evidence.readiness_gates import ReadinessGatesEngine


def test_descriptive_stats_with_sample_size():
    """Verify descriptive statistics displays sample size N, mean, median, IQR, CV."""
    vals = [10.0, 12.0, 15.0, 18.0, 20.0, None]
    stats_res = calculate_descriptive_stats("temp", vals, unit="°C")
    assert stats_res.sample_size_n == 5
    assert stats_res.missing_count == 1
    assert stats_res.mean == 15.0
    assert stats_res.median == 15.0
    assert stats_res.iqr is not None


def test_pearson_and_spearman_correlation():
    """Verify Pearson & Spearman correlation matrices with small sample size warnings."""
    rows = [
        {"temp": 300.0, "cond": 1.2},
        {"temp": 350.0, "cond": 3.4},
        {"temp": 400.0, "cond": 5.8},
    ]
    res_pearson = calculate_correlation_matrix(["temp", "cond"], rows, method="PEARSON")
    assert res_pearson.matrix["temp"]["cond"] > 0.95
    assert len(res_pearson.warnings) > 0

    res_spearman = calculate_correlation_matrix(["temp", "cond"], rows, method="SPEARMAN")
    assert res_spearman.matrix["temp"]["cond"] == 1.0


def test_regression_model_fitting_and_diagnostics():
    """Verify linear, interaction, and quadratic regression model fitting and Q-Q diagnostics."""
    rows = [
        {"temp": 300.0, "rate": 2.0, "cond": 1.2},
        {"temp": 300.0, "rate": 5.0, "cond": 2.1},
        {"temp": 400.0, "rate": 2.0, "cond": 4.5},
        {"temp": 400.0, "rate": 5.0, "cond": 5.8},
    ]
    reg_res = fit_regression_model(["temp", "rate"], "cond", rows, include_interaction=True)
    assert reg_res.r_squared > 0.95
    assert "temp:rate" in reg_res.coefficients

    residuals = [0.05, -0.05, 0.08, -0.08]
    fitted_values = [1.15, 2.15, 4.42, 5.88]
    diag = ModelDiagnosticsEngine.compute_diagnostics(residuals, fitted_values)
    assert len(diag.qq_sample_quantiles) == 4


def test_confidence_vs_prediction_intervals():
    """Verify distinction between 95% Confidence Intervals and 95% Prediction Intervals."""
    y_vals = [1.2, 2.1, 4.5, 5.8]
    y_pred = [1.15, 2.15, 4.45, 5.85]
    ci, pi = EffectEstimationEngine.calculate_confidence_and_prediction_intervals(y_vals, y_pred, p_predictors=1)

    ci_width = ci["upper"][0] - ci["lower"][0]
    pi_width = pi["upper"][0] - pi["lower"][0]
    # Prediction interval width includes observation variability and must be >= Confidence interval width
    assert pi_width >= ci_width


def test_outlier_flagging_without_deletion():
    """Verify outlier detection flags potential outliers without modifying original data."""
    records = [("s1", "S-01", 10.0), ("s2", "S-02", 11.0), ("s3", "S-03", 12.0), ("s4", "S-04", 100.0)]
    outlier_res = detect_outliers_iqr_or_zscore("conductivity", records, method="IQR", threshold=1.5)
    assert len(outlier_res.outliers_found) == 1
    assert outlier_res.outliers_found[0].sample_code == "S-04"
    assert outlier_res.outliers_found[0].is_excluded is False


def test_conservative_statement_formulation():
    """Verify conservative scientific statement formulation avoids unsupported causality claims."""
    stmt = EvidenceEngine.generate_conservative_statement(
        ["substrate_temperature", "conductivity_s_cm"],
        "ASSOCIATION",
        0.89,
        "Pearson Correlation",
        sample_size=8,
    )
    assert "positive association" in stmt
    assert "causes" not in stmt


def test_evidence_scoring_logic():
    """Verify transparent evidence score calculation."""
    score, criteria = EvidenceEngine.compute_evidence_score(
        sample_size=8, has_replicates=True, missing_rate=0.0, r_squared=0.9
    )
    assert score >= 70.0
    assert criteria["quality_category"] == "HIGH"


def test_readiness_gates_evaluation():
    """Verify ML-Ready & Optimization-Ready status gate evaluation."""
    gates = ReadinessGatesEngine.evaluate_gates("dv-001", sample_size=10, missing_rate=0.05, quality_status="PASS", has_validated_model=True)
    assert gates.is_ml_ready is True
    assert gates.is_optimization_ready is True
    assert "software validation quality gates" in gates.disclaimer
