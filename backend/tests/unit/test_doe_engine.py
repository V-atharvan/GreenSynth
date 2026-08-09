"""
GreenSynth Analytics — DOE Engine Unit Tests
"""

import pytest

from app.optimization.doe.constraints import evaluate_candidate_constraints
from app.optimization.doe.factorial import generate_full_factorial_matrix
from app.optimization.doe.random_design import generate_random_candidates
from app.optimization.doe.response_surface import generate_box_behnken_matrix, generate_ccd_matrix
from app.optimization.doe.schemas import DOEConstraint, FactorDefinition


def test_full_factorial_2x3():
    f1 = FactorDefinition(
        parameter_code="substrate_temperature",
        name="Temperature",
        factor_type="CONTINUOUS",
        lower_bound=250.0,
        upper_bound=400.0,
        levels=3,
    )
    f2 = FactorDefinition(
        parameter_code="spray_rate",
        name="Spray Rate",
        factor_type="CONTINUOUS",
        lower_bound=1.0,
        upper_bound=5.0,
        levels=3,
    )
    matrix = generate_full_factorial_matrix([f1, f2])

    assert len(matrix) == 9  # 3 * 3 = 9
    temps = {row["substrate_temperature"] for row in matrix}
    assert temps == {250.0, 325.0, 400.0}


def test_ccd_generation():
    f1 = FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=100.0, upper_bound=200.0)
    f2 = FactorDefinition(parameter_code="conc", name="Conc", factor_type="CONTINUOUS", lower_bound=1.0, upper_bound=5.0)

    matrix = generate_ccd_matrix([f1, f2], alpha=1.0)
    # 2^2 factorial (4) + 2*2 axial (4) + center (1) = 9 points
    assert len(matrix) == 9


def test_randomized_candidates_seed_reproducibility():
    f1 = FactorDefinition(parameter_code="temp", name="Temp", factor_type="CONTINUOUS", lower_bound=250.0, upper_bound=400.0)
    f2 = FactorDefinition(parameter_code="solvent", name="Solvent", factor_type="CATEGORICAL", levels=["Ethanol", "Acetone"])

    runs_seed1_a = generate_random_candidates([f1, f2], requested_runs=5, random_seed=123)
    runs_seed1_b = generate_random_candidates([f1, f2], requested_runs=5, random_seed=123)
    runs_seed2 = generate_random_candidates([f1, f2], requested_runs=5, random_seed=456)

    assert runs_seed1_a == runs_seed1_b  # Exact match
    assert runs_seed1_a != runs_seed2    # Different seed yields different candidate sequence


def test_constraint_evaluation():
    constraints = [
        DOEConstraint(parameter_code="temp", operator="BETWEEN", value=[250.0, 400.0]),
        DOEConstraint(parameter_code="spray_rate", operator="<=", value=5.0),
    ]

    valid_res, errs1 = evaluate_candidate_constraints({"temp": 300.0, "spray_rate": 3.0}, constraints)
    assert valid_res is True
    assert len(errs1) == 0

    invalid_res, errs2 = evaluate_candidate_constraints({"temp": 450.0, "spray_rate": 6.0}, constraints)
    assert invalid_res is False
    assert len(errs2) == 2
