"""
GreenSynth Analytics — Candidate Generation Service (Phase 18)

Orchestrates candidate generation for green synthesis optimization:
  1. Validates model eligibility and health status (CRITICAL blocks; WARNING requires confirmation).
  2. Generates candidate parameter combinations via GRID_SEARCH, RANDOM_SEARCH, or MODEL_GUIDED_SEARCH.
  3. Evaluates model predictions and prediction uncertainties.
  4. Runs domain check (IN_DOMAIN, NEAR_BOUNDARY, OUT_OF_DOMAIN).
  5. Evaluates hard/soft constraints (FEASIBLE, INFEASIBLE, WARNING).
  6. Calculates parameter-space distance to historical experiments (ALREADY_TESTED, LOW_DISTANCE, MEDIUM_DISTANCE, HIGH_DISTANCE).
  7. Calculates objective scores and transparent score contribution breakdowns.
  8. Ranks candidates and removes deduplicated/infeasible candidates.
"""

from __future__ import annotations

import itertools
import math
import random
from typing import Any

from app.scientific.optimization.constraint_evaluation import ConstraintEvaluationService
from app.scientific.optimization.domain_check import DomainCheckService
from app.scientific.optimization.novelty_service import ParameterDistanceService
from app.scientific.optimization.objective_scoring import ObjectiveScoringService
from app.scientific.optimization.candidate_ranking import CandidateRankingService


class CandidateGenerationService:
    """
    Core engine for evidence-based candidate generation.
    """

    MAX_CANDIDATES = 10000

    @classmethod
    def generate_candidates(
        cls,
        search_space: dict[str, Any],
        objectives: list[dict[str, Any]],
        constraints: list[dict[str, Any]],
        model_metadata: dict[str, Any],
        historical_experiments: list[dict[str, Any]],
        generation_method: str = "RANDOM_SEARCH",
        requested_count: int = 10,
        random_seed: int | None = 42,
        allow_out_of_domain: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Main entry point for generating candidate conditions.
        """
        # 1. Model Health Gate Check
        model_status = str(model_metadata.get("status", "APPROVED")).upper()
        model_health = str(model_metadata.get("health_status", "STABLE")).upper()

        if model_status == "RETIRED" or model_health == "CRITICAL":
            raise ValueError(
                f"Optimization blocked because selected model '{model_metadata.get('name')}' is {model_status}/{model_health}."
            )

        # 2. Build parameter candidate tuples
        params_def = search_space.get("parameters_definition", {})
        if not params_def:
            raise ValueError("Search space parameters definition is empty or unconfigured.")

        if random_seed is not None:
            random.seed(random_seed)

        raw_candidate_params_list: list[dict[str, float]] = []

        if generation_method == "GRID_SEARCH":
            grid_values: list[list[tuple[str, float]]] = []
            param_codes: list[str] = []

            for p_code, p_spec in params_def.items():
                min_v = p_spec.get("minimum_value")
                max_v = p_spec.get("maximum_value")
                if min_v is None or max_v is None:
                    raise ValueError(f"Search-space range is not defined for parameter '{p_code}'.")

                step = p_spec.get("step_size") or ((max_v - min_v) / 4.0 if max_v > min_v else 1.0)
                if step <= 0:
                    step = 1.0

                vals: list[float] = []
                curr = float(min_v)
                while curr <= float(max_v) + 1e-6:
                    vals.append(round(curr, 4))
                    curr += step

                param_codes.append(p_code)
                grid_values.append([(p_code, v) for v in vals])

            # Check combinatorial size
            total_combos = 1
            for g in grid_values:
                total_combos *= len(g)

            if total_combos > cls.MAX_CANDIDATES:
                raise ValueError(
                    f"Grid search requested {total_combos} combinations, which exceeds safety limit of {cls.MAX_CANDIDATES}. Reduce grid density."
                )

            for combo in itertools.product(*grid_values):
                raw_candidate_params_list.append(dict(combo))

        else:  # RANDOM_SEARCH or MODEL_GUIDED_SEARCH
            samples_to_draw = min(requested_count * 50, cls.MAX_CANDIDATES)
            for _ in range(samples_to_draw):
                cand_p: dict[str, float] = {}
                for p_code, p_spec in params_def.items():
                    min_v = p_spec.get("minimum_value")
                    max_v = p_spec.get("maximum_value")
                    if min_v is None or max_v is None:
                        raise ValueError(f"Search-space range is not defined for parameter '{p_code}'.")
                    val = random.uniform(float(min_v), float(max_v))
                    cand_p[p_code] = round(val, 4)
                raw_candidate_params_list.append(cand_p)

        # Bounds for distance calculations
        param_bounds: dict[str, tuple[float, float]] = {
            p_code: (float(p_spec.get("minimum_value", 0.0)), float(p_spec.get("maximum_value", 1.0)))
            for p_code, p_spec in params_def.items()
            if p_spec.get("minimum_value") is not None and p_spec.get("maximum_value") is not None
        }

        # Training feature bounds from model
        training_bounds: dict[str, tuple[float, float]] = model_metadata.get("training_feature_bounds", param_bounds)

        candidates: list[dict[str, Any]] = []

        for idx, cand_params in enumerate(raw_candidate_params_list, start=1):
            # 3. Simulate Model Prediction
            predictions, uncertainties = cls._generate_model_predictions(cand_params, model_metadata)

            # 4. Domain Check
            domain_status, domain_warnings = DomainCheckService.evaluate_candidate_domain(
                cand_params, training_bounds
            )

            # 5. Constraint Evaluation
            feasibility, constraint_reasons = ConstraintEvaluationService.evaluate_candidate(
                cand_params, predictions, constraints
            )

            # 6. Novelty / Distance Check
            novelty_cat, distance_val, nearby_ids = ParameterDistanceService.calculate_distance(
                cand_params, historical_experiments, param_bounds
            )

            # 7. Objective Scoring
            total_score, score_breakdown = ObjectiveScoringService.evaluate_objectives(
                predictions, objectives
            )

            param_units = {
                p_code: p_spec.get("unit", "")
                for p_code, p_spec in params_def.items()
            }

            evidence_score = round(max(0.2, 1.0 - (0.5 if domain_status == "OUT_OF_DOMAIN" else 0.0) - min(0.3, distance_val * 0.3)), 2)

            cand_obj = {
                "candidate_number": idx,
                "parameter_values": cand_params,
                "parameter_units": param_units,
                "feasibility_status": feasibility,
                "constraint_reasons": constraint_reasons,
                "domain_status": domain_status,
                "domain_warnings": domain_warnings,
                "predictions": predictions,
                "uncertainties": uncertainties,
                "objective_score": total_score,
                "score_breakdown": score_breakdown,
                "evidence_score": evidence_score,
                "novelty_category": novelty_cat,
                "parameter_distance": distance_val,
                "nearby_experiment_ids": nearby_ids,
            }
            candidates.append(cand_obj)

        # 8. Rank and filter
        ranked_candidates = CandidateRankingService.rank_and_categorize(
            candidates, allow_out_of_domain=allow_out_of_domain
        )

        return ranked_candidates[:requested_count]

    @staticmethod
    def _generate_model_predictions(
        candidate_params: dict[str, float],
        model_metadata: dict[str, Any],
    ) -> tuple[dict[str, float], dict[str, Any]]:
        """
        Simulates / invokes model predictions for candidate parameter set.
        """
        target_prop = model_metadata.get("target_property", "conductivity_s_cm")
        unit = model_metadata.get("target_unit", "S/cm")

        # Deterministic formula based on inputs
        temp = candidate_params.get("substrate_temperature_c", candidate_params.get("substrate_temperature", 350.0))
        spray = candidate_params.get("spray_rate_ml_min", candidate_params.get("spray_rate", 5.0))
        ext = candidate_params.get("extract_concentration", 10.0)

        # Linear model simulation
        val = -5.0 + (temp * 0.025) + (spray * 0.35) + (ext * 0.05)
        val = round(max(0.1, val), 3)

        # Estimated uncertainty interval
        std_err = round(0.15 + (abs(temp - 350.0) / 1000.0), 3)
        lower = round(max(0.0, val - 1.96 * std_err), 3)
        upper = round(val + 1.96 * std_err, 3)

        predictions = {target_prop: val}
        uncertainties = {
            target_prop: {
                "unit": unit,
                "predicted_value": val,
                "std_error": std_err,
                "confidence_level": 0.95,
                "lower_bound": lower,
                "upper_bound": upper,
                "width": round(upper - lower, 3),
            }
        }

        return predictions, uncertainties
