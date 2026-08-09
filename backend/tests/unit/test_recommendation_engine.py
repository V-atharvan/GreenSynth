"""
GreenSynth Analytics — Unit Tests: Recommendation Engine (Gates, Constraints, Domain, Evidence, Ranking, Modification)
"""

from __future__ import annotations

import uuid
import pytest

from app.models.doe import Objective
from app.models.ml import MLDatasetRecord, MLModel
from app.models.project import Project
from app.optimization.recommendation.candidate_ranker import CandidateRanker
from app.optimization.recommendation.constraint_engine import ConstraintEngine
from app.optimization.recommendation.diversity_selector import DiversitySelector
from app.optimization.recommendation.domain_checker import DomainChecker
from app.optimization.recommendation.evidence_engine import EvidenceEngine


def test_constraint_engine_safety_and_ranges():
    engine = ConstraintEngine()
    proj = Project(
        id=uuid.uuid4(),
        project_code="P7-RECS",
        name="Project 7",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
    )
    obj = Objective(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="Maximize Conductivity",
        target_property="Electrical Conductivity",
        direction="MAXIMIZE",
        constraints=[
            {"parameter": "substrate_temperature", "operator": "<=", "value": 400.0},
            {"parameter": "substrate_temperature", "operator": ">=", "value": 250.0},
        ],
    )

    # Valid candidate
    res1 = engine.evaluate({"substrate_temperature": 350.0, "spray_rate": 2.5}, obj, proj)
    assert res1.is_valid is True
    assert res1.status == "SATISFIED"

    # Safety violation: Temperature <= 0
    res2 = engine.evaluate({"substrate_temperature": -10.0, "spray_rate": 2.5}, obj, proj)
    assert res2.is_valid is False
    assert res2.status == "HARD_VIOLATION"

    # Range constraint violation: Temperature 450 > 400
    res3 = engine.evaluate({"substrate_temperature": 450.0, "spray_rate": 2.5}, obj, proj)
    assert res3.is_valid is False
    assert res3.status == "HARD_VIOLATION"


def test_domain_checker():
    checker = DomainChecker()
    feature_specs = [{"feature_name": "temp"}]

    training_records = [
        MLDatasetRecord(
            id=uuid.uuid4(),
            dataset_id=uuid.uuid4(),
            experiment_id=uuid.uuid4(),
            sample_id=uuid.uuid4(),
            feature_values={"temp": 300.0},
            target_value=5.0,
            is_eligible=True,
        ),
        MLDatasetRecord(
            id=uuid.uuid4(),
            dataset_id=uuid.uuid4(),
            experiment_id=uuid.uuid4(),
            sample_id=uuid.uuid4(),
            feature_values={"temp": 400.0},
            target_value=8.0,
            is_eligible=True,
        ),
    ]

    # In domain point (close to 300)
    res1 = checker.check_domain({"temp": 310.0}, training_records, feature_specs)
    assert res1.status in ("IN_DOMAIN", "NEAR_BOUNDARY")
    assert res1.is_in_domain is True

    # Out of domain point
    res2 = checker.check_domain({"temp": 450.0}, training_records, feature_specs)
    assert res2.status == "OUT_OF_DOMAIN"
    assert res2.is_in_domain is False


def test_evidence_engine():
    engine = EvidenceEngine()

    model = MLModel(
        id=uuid.uuid4(),
        training_run_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
        dataset_version="v1",
        name="CuO Model",
        model_type="LINEAR_REGRESSION",
        version="1.0",
        target_property="Electrical Conductivity",
        target_type="CALCULATED",
        target_unit="S/cm",
        feature_names=["temp"],
        feature_specs=[],
        preprocessing_config={},
        hyperparameters={},
        artifact_path="data/models/test/model.joblib",
        metrics={"cv_r2": 0.85},
        library_versions={},
        status="VALIDATED",
    )

    # In-domain + physical validations -> HIGH evidence
    res1 = engine.evaluate_evidence(
        model=model,
        domain_status="IN_DOMAIN",
        distance_to_nearest=0.1,
        n_physical_validations=5,
    )
    assert res1.evidence_level == "HIGH"
    assert res1.evidence_score >= 0.7

    # Out-of-domain -> LOW evidence
    res2 = engine.evaluate_evidence(
        model=model,
        domain_status="OUT_OF_DOMAIN",
        distance_to_nearest=0.9,
        n_physical_validations=0,
    )
    assert res2.evidence_level == "LOW"
    assert res2.evidence_score < 0.4


def test_candidate_ranker():
    ranker = CandidateRanker()
    obj = Objective(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        name="Maximize Conductivity",
        target_property="Electrical Conductivity",
        direction="MAXIMIZE",
        target_value=5.0,
    )

    # Exploitation vs Exploration strategy
    res_exp = ranker.score_candidate(
        predicted_val=7.5,
        objective=obj,
        constraint_penalty=0.0,
        evidence_score=0.8,
        distance_to_nearest=0.1,
        uncertainty_width=0.4,
        strategy="EXPLOITATION",
    )
    assert res_exp.objective_score > 0.7
    assert res_exp.overall_score >= 0.6


def test_diversity_selector():
    selector = DiversitySelector()

    cands = [
        {"parameter_set": {"temp": 350.0, "rate": 2.0}},
        {"parameter_set": {"temp": 350.5, "rate": 2.01}},  # Near duplicate
        {"parameter_set": {"temp": 450.0, "rate": 4.0}},   # Diverse
    ]

    selected = selector.select_diverse_subset(cands, parameter_names=["temp", "rate"], top_n=2)
    assert len(selected) == 2
    assert selected[0]["parameter_set"]["temp"] == 350.0
    assert selected[1]["parameter_set"]["temp"] == 450.0
