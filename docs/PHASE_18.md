# Phase 18 — Evidence-Based Experimental Optimization and Candidate Generation

## Overview
Phase 18 implements an evidence-based experimental optimization engine for green semiconductor synthesis. It translates validated ML models, historical experimental records, researcher objectives, and synthesis constraints into ranked candidate experimental conditions.

## Core Architecture Workflow
```
HISTORICAL EXPERIMENTS
        ↓
VALIDATED DATA
        ↓
APPROVED MODEL
        ↓
RESEARCHER OBJECTIVE
        ↓
EXPERIMENTAL CONSTRAINTS
        ↓
SEARCH SPACE
        ↓
CANDIDATE GENERATION
        ↓
MODEL PREDICTIONS
        ↓
UNCERTAINTY
        ↓
FEASIBILITY CHECK
        ↓
OBJECTIVE SCORING
        ↓
CANDIDATE RANKING
        ↓
EVIDENCE DISPLAY
        ↓
RESEARCHER REVIEW
        ↓
SELECT CANDIDATE
        ↓
PROPOSED EXPERIMENT
        ↓
LABORATORY EXPERIMENT
        ↓
ACTUAL RESULT
        ↓
PHASE 17 VALIDATION
```

## Mandatory Scientific Disclaimer
Optimization is **NOT** experimental proof. All candidate conditions are model-predicted estimates requiring physical laboratory validation. Candidate conditions are described as **promising candidates**, never as "proven optimal" or "guaranteed".

## Components
1. **ORM Models** (`app/models/optimization.py`):
   `OptimizationObjective`, `OptimizationConstraint`, `OptimizationSearchSpace`, `OptimizationRun`, `OptimizationCandidate`, `CandidatePrediction`, `CandidateExperimentLink`, `CandidateEvidenceSnapshot`, `OptimizationReview`.
2. **Scientific Services** (`app/scientific/optimization/`):
   - `CandidateGenerationService` (Grid Search, Random Search with seed, Model-guided Search)
   - `ObjectiveScoringService` (MAXIMIZE, MINIMIZE, TARGET, weighted multi-objective scoring)
   - `ConstraintEvaluationService` (Hard/soft feasibility evaluation)
   - `DomainCheckService` (IN_DOMAIN, NEAR_BOUNDARY, OUT_OF_DOMAIN)
   - `ParameterDistanceService` (ALREADY_TESTED, LOW_DISTANCE, MEDIUM_DISTANCE, HIGH_DISTANCE)
   - `CandidateRankingService` (Feasibility filtering, score ranking, EXPLOITATION vs EXPLORATION)
3. **API Router** (`app/api/routes/optimization.py`):
   `/api/v1/optimization/objectives`, `/constraints`, `/search-space/validate`, `/runs`, `/candidates`, `/candidates/{id}/create-experiment`, `/runs/{id}/report`.
4. **Frontend Optimization Studio** (`frontend/src/pages/OptimizationStudio.tsx`):
   Configurators, Search Space validator, Model Health Gate check (CRITICAL block / WARNING confirmation), Candidate Table, Detail Modal, Tradeoff Visualizer, Proposed Experiment Converter.
