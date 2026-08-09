"""
GreenSynth Analytics — Phase 18 Optimization Unit Tests
"""

import pytest
from app.scientific.optimization.constraint_evaluation import ConstraintEvaluationService
from app.scientific.optimization.domain_check import DomainCheckService
from app.scientific.optimization.novelty_service import ParameterDistanceService
from app.scientific.optimization.objective_scoring import ObjectiveScoringService
from app.scientific.optimization.candidate_generation import CandidateGenerationService


def test_objective_scoring_maximize():
    score = ObjectiveScoringService.score_single_objective(
        prediction_val=3.5, direction="MAXIMIZE", min_val=0.0, max_val=5.0
    )
    assert score == pytest.approx(0.7, 0.01)


def test_objective_scoring_minimize():
    score = ObjectiveScoringService.score_single_objective(
        prediction_val=2.0, direction="MINIMIZE", min_val=0.0, max_val=10.0
    )
    assert score == pytest.approx(0.8, 0.01)


def test_objective_scoring_target():
    score = ObjectiveScoringService.score_single_objective(
        prediction_val=1.50, direction="TARGET", target_val=1.50, min_val=1.0, max_val=2.0
    )
    assert score == pytest.approx(1.0, 0.01)


def test_multi_objective_normalized_weight_scoring():
    predictions = {"conductivity_s_cm": 4.0, "band_gap_ev": 1.50}
    objectives = [
        {"target_property": "conductivity_s_cm", "direction": "MAXIMIZE", "min_value": 0.0, "max_value": 5.0, "weight": 0.6},
        {"target_property": "band_gap_ev", "direction": "TARGET", "target_value": 1.50, "min_value": 1.0, "max_value": 2.0, "weight": 0.4},
    ]

    total_score, breakdown = ObjectiveScoringService.evaluate_objectives(predictions, objectives)

    assert total_score > 0.8
    assert breakdown["contributions"]["conductivity_s_cm"]["normalized_weight"] == 0.6
    assert breakdown["contributions"]["band_gap_ev"]["normalized_weight"] == 0.4


def test_hard_constraint_evaluation_infeasible():
    candidate_params = {"substrate_temperature_c": 450.0}
    predictions = {}
    constraints = [
        {
            "constraint_type": "PARAMETER_RANGE",
            "target_code": "substrate_temperature_c",
            "minimum_value": 300.0,
            "maximum_value": 400.0,
            "is_hard_constraint": True,
        }
    ]

    status, reasons = ConstraintEvaluationService.evaluate_candidate(candidate_params, predictions, constraints)
    assert status == "INFEASIBLE"
    assert len(reasons) > 0


def test_domain_check_out_of_domain():
    candidate_params = {"substrate_temperature_c": 450.0}
    bounds = {"substrate_temperature_c": (300.0, 400.0)}

    status, warnings = DomainCheckService.evaluate_candidate_domain(candidate_params, bounds)
    assert status == "OUT_OF_DOMAIN"
    assert len(warnings) > 0


def test_already_tested_experiment_detection():
    candidate_params = {"substrate_temperature_c": 350.0, "spray_rate_ml_min": 5.0}
    historical_exps = [
        {"id": "exp-001", "parameter_values": {"substrate_temperature_c": 350.0, "spray_rate_ml_min": 5.0}}
    ]
    bounds = {"substrate_temperature_c": (300.0, 400.0), "spray_rate_ml_min": (1.0, 10.0)}

    novelty, dist, exps = ParameterDistanceService.calculate_distance(candidate_params, historical_exps, bounds)
    assert novelty == "ALREADY_TESTED"
    assert dist == 0.0
    assert "exp-001" in exps


def test_random_seed_reproducibility():
    search_space = {
        "parameters_definition": {
            "substrate_temperature_c": {"minimum_value": 300.0, "maximum_value": 400.0, "unit": "°C"},
            "spray_rate_ml_min": {"minimum_value": 2.0, "maximum_value": 8.0, "unit": "mL/min"},
        }
    }
    objs = [{"target_property": "conductivity_s_cm", "direction": "MAXIMIZE", "weight": 1.0}]
    model_meta = {"name": "TestModel", "status": "APPROVED", "health_status": "STABLE", "target_property": "conductivity_s_cm"}

    cands_run1 = CandidateGenerationService.generate_candidates(
        search_space=search_space,
        objectives=objs,
        constraints=[],
        model_metadata=model_meta,
        historical_experiments=[],
        generation_method="RANDOM_SEARCH",
        requested_count=5,
        random_seed=12345,
    )

    cands_run2 = CandidateGenerationService.generate_candidates(
        search_space=search_space,
        objectives=objs,
        constraints=[],
        model_metadata=model_meta,
        historical_experiments=[],
        generation_method="RANDOM_SEARCH",
        requested_count=5,
        random_seed=12345,
    )

    assert len(cands_run1) == len(cands_run2) == 5
    for c1, c2 in zip(cands_run1, cands_run2):
        assert c1["parameter_values"] == c2["parameter_values"]
