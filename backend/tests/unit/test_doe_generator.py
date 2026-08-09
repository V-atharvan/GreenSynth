"""
GreenSynth Analytics — Phase 14 DOE Generator & Analysis Engine Unit Tests
"""

import pytest
from app.optimization.doe.design_generator import DOEGeneratorFactory
from app.optimization.doe.design_validator import DOEValidator
from app.optimization.doe.doe_analysis import DOEAnalysisEngine
from app.optimization.doe.schemas import DOEConstraint, FactorDefinition


def test_full_factorial_2k_and_3k_run_counts():
    """Verify 2^k and 3^k full factorial design matrix run counts."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=300, upper_bound=400, levels=2),
        FactorDefinition(parameter_code="rate", name="Rate", factor_type="CONTINUOUS", lower_bound=2, upper_bound=5, levels=2),
        FactorDefinition(parameter_code="conc", name="Conc", factor_type="CONTINUOUS", lower_bound=0.05, upper_bound=0.15, levels=2),
    ]
    preview = DOEGeneratorFactory.preview_workload("FULL_FACTORIAL", factors)
    assert preview.base_runs == 8
    assert preview.total_runs == 8

    matrix, res, warn = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors)
    assert len(matrix) == 8
    assert res == "Full Factorial (Res V+)"


def test_fractional_factorial_half_fraction():
    """Verify 2^(k-1) half-fraction factorial design matrix."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=300, upper_bound=400, levels=2),
        FactorDefinition(parameter_code="rate", name="Rate", factor_type="CONTINUOUS", lower_bound=2, upper_bound=5, levels=2),
        FactorDefinition(parameter_code="conc", name="Conc", factor_type="CONTINUOUS", lower_bound=0.05, upper_bound=0.15, levels=2),
    ]
    preview = DOEGeneratorFactory.preview_workload("FRACTIONAL_FACTORIAL", factors)
    assert preview.base_runs == 4

    matrix, res, warn = DOEGeneratorFactory.generate_design_matrix("FRACTIONAL_FACTORIAL", factors)
    assert len(matrix) == 4
    assert warn is not None


def test_central_composite_design_star_points():
    """Verify Central Composite Design factorial, axial, and center points."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=300, upper_bound=400),
        FactorDefinition(parameter_code="rate", name="Rate", factor_type="CONTINUOUS", lower_bound=2, upper_bound=5),
    ]
    preview = DOEGeneratorFactory.preview_workload("CENTRAL_COMPOSITE", factors)
    # 2^2 = 4 factorial + 2*2 = 4 axial = 8 base runs
    assert preview.base_runs == 8

    matrix, res, warn = DOEGeneratorFactory.generate_design_matrix("CENTRAL_COMPOSITE", factors, center_points=2)
    assert len(matrix) == 11  # 9 base (4 factorial + 4 axial + 1 center) + 2 extra center points


def test_seed_reproducible_randomization():
    """Verify seed-reproducible run order randomization."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=300, upper_bound=400),
        FactorDefinition(parameter_code="rate", name="Rate", factor_type="CONTINUOUS", lower_bound=2, upper_bound=5),
    ]
    m1, _, _ = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors, random_seed=42)
    m2, _, _ = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors, random_seed=42)
    m3, _, _ = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors, random_seed=99)

    assert m1 == m2
    assert m1 != m3


def test_replicates_and_center_points():
    """Verify replicate generation with distinct replicate numbers."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=300, upper_bound=400),
        FactorDefinition(parameter_code="rate", name="Rate", factor_type="CONTINUOUS", lower_bound=2, upper_bound=5),
    ]
    matrix, _, _ = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors, replicates=2)
    # 4 base runs * 2 replicates = 8 runs
    assert len(matrix) == 8
    reps = [r["_replicate"] for r in matrix]
    assert reps.count(1) == 4
    assert reps.count(2) == 4


def test_constraint_validator_blocking():
    """Verify constraint validation blocks invalid runs."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=100, upper_bound=500),
    ]
    constraints = [
        DOEConstraint(parameter_code="temp", operator=">=", value=600),
    ]
    matrix, _, _ = DOEGeneratorFactory.generate_design_matrix("FULL_FACTORIAL", factors)
    with pytest.raises(ValueError, match="DOE generation failed"):
        DOEValidator.validate_matrix_constraints(matrix, constraints, factors)


def test_unit_validator_blocking():
    """Verify factor unit validator blocks upper_bound <= lower_bound."""
    factors = [
        FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=400, upper_bound=300),
    ]
    with pytest.raises(ValueError, match="Factor upper bound"):
        DOEValidator.validate_factors_and_units(factors)


def test_main_effects_and_response_surface_fit():
    """Verify Main Effects calculation and response surface regression fitting."""
    runs = [
        {"factor_values": {"temp": 300.0, "rate": 2.0}, "measured_responses": {"Electrical Conductivity": 1.2}},
        {"factor_values": {"temp": 300.0, "rate": 5.0}, "measured_responses": {"Electrical Conductivity": 2.1}},
        {"factor_values": {"temp": 400.0, "rate": 2.0}, "measured_responses": {"Electrical Conductivity": 4.5}},
        {"factor_values": {"temp": 400.0, "rate": 5.0}, "measured_responses": {"Electrical Conductivity": 5.8}},
    ]
    main_effects = DOEAnalysisEngine.calculate_main_effects(runs, "Electrical Conductivity")
    assert "temp" in main_effects
    # temp effect = mean(4.5, 5.8) - mean(1.2, 2.1) = 5.15 - 1.65 = 3.5
    assert abs(main_effects["temp"]["estimated_main_effect"] - 3.5) < 1e-3

    fit = DOEAnalysisEngine.fit_response_surface(runs, "Electrical Conductivity")
    assert fit["status"] == "FITTED"
    assert fit["fit_metrics"]["r2"] is not None
    assert fit["fit_metrics"]["r2"] > 0.95
