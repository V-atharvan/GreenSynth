"""
GreenSynth Analytics — Scientific Unit Tests: Statistics & Analytics Engine
"""

from __future__ import annotations

import uuid

import numpy as np
import pytest

from app.analytics.statistics.correlation import CorrelationError, calculate_pearson_correlation
from app.analytics.statistics.descriptive import calculate_descriptive_stats
from app.analytics.statistics.group_comparison import calculate_group_comparison
from app.analytics.statistics.outliers import detect_outliers_iqr
from app.analytics.statistics.regression import RegressionError, calculate_linear_regression


def test_descriptive_statistics() -> None:
    """Verify count (n), mean, median, std_dev, min, max, and missing count."""
    vals = [10.0, 20.0, 30.0, 40.0, 50.0, None]
    res = calculate_descriptive_stats("substrate_temperature", vals)

    assert res.sample_size_n == 5
    assert res.missing_count == 1
    assert res.mean == 30.0
    assert res.median == 30.0
    assert res.min_val == 10.0
    assert res.max_val == 50.0
    assert res.val_range == 40.0
    assert res.std_dev is not None and abs(res.std_dev - 15.8114) < 0.01


def test_pearson_correlation() -> None:
    """Verify Pearson correlation coefficient r, p-value, and caution disclaimers."""
    # Perfect linear relationship y = 2x + 1
    x_vals = [100.0, 200.0, 300.0, 400.0, 500.0]
    y_vals = [2.0, 4.0, 6.0, 8.0, 10.0]

    res = calculate_pearson_correlation("substrate_temperature", "conductivity_s_cm", x_vals, y_vals)

    assert res.sample_size_n == 5
    assert res.pearson_r == 1.0
    assert res.p_value is not None and res.p_value < 0.001
    assert "Strong positive linear association" in res.interpretation
    assert any("does not establish causation" in w for w in res.warnings)


def test_pearson_correlation_insufficient_data() -> None:
    """< 3 paired points raises CorrelationError."""
    with pytest.raises(CorrelationError, match="Insufficient valid paired data points"):
        calculate_pearson_correlation("temp", "conductivity", [100.0, 200.0], [2.0, 4.0])


def test_linear_regression_engine() -> None:
    """Verify OLS linear regression fit (Y = slope * X + intercept), R^2, MAE, and RMSE."""
    x_vals = [250.0, 300.0, 350.0, 400.0, 450.0]
    # Y = 0.02 * X - 1.0
    y_vals = [4.0, 5.0, 6.0, 7.0, 8.0]

    res = calculate_linear_regression("substrate_temperature", "conductivity_s_cm", x_vals, y_vals)

    assert res.sample_size_n == 5
    assert abs(res.slope - 0.02) < 0.001
    assert abs(res.intercept - (-1.0)) < 0.001
    assert res.r_squared == 1.0
    assert "conductivity_s_cm = 0.0200 * substrate_temperature - 1.0000" in res.formula
    assert any("not a universal physical law" in w for w in res.warnings)


def test_group_comparison_engine() -> None:
    """Verify grouping by categorical factor (e.g. Solvent) and per-group statistics."""
    group_vals = ["Ethanol", "Ethanol", "Ethanol", "Water", "Water"]
    target_vals = [5.0, 5.2, 5.4, 2.0, 2.2]

    res = calculate_group_comparison("solvent", "conductivity_s_cm", group_vals, target_vals)

    assert len(res.groups) == 2
    eth_group = next(g for g in res.groups if g.group_value == "Ethanol")
    water_group = next(g for g in res.groups if g.group_value == "Water")

    assert eth_group.sample_size_n == 3
    assert abs(eth_group.mean - 5.2) < 0.01
    assert water_group.sample_size_n == 2
    assert abs(water_group.mean - 2.1) < 0.01
    assert "highest mean value" in res.interpretation


def test_outlier_detection_iqr() -> None:
    """Verify 1.5 * IQR rule outlier identification."""
    sample_ids = [uuid.uuid4() for _ in range(7)]
    sample_codes = [f"S00{i}" for i in range(1, 8)]
    vals = [10.0, 11.0, 12.0, 11.5, 12.5, 10.8, 100.0]  # 100.0 is an extreme outlier

    res = detect_outliers_iqr("band_gap_ev", sample_ids, sample_codes, vals)

    assert res.total_inspected == 7
    assert len(res.outliers_found) == 1
    assert res.outliers_found[0].sample_code == "S007"
    assert res.outliers_found[0].value == 100.0
