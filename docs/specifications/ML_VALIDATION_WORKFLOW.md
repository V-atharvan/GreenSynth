# Phase 17: Closed-Loop Experimental Prediction Validation Workflow

## 1. Complete Workflow Diagram
```
APPROVED MODEL
        ↓
PREDICTION (predicted_value, uncertainty, bounds)
        ↓
RESEARCHER PERFORMS EXPERIMENT
        ↓
ACTUAL EXPERIMENT (actual_synthesis_parameters)
        ↓
CHARACTERIZATION & SCIENTIFIC ANALYSIS (actual_measured_value)
        ↓
TARGET & UNIT COMPATIBILITY CHECK
        ↓
CONDITION DEVIATION EVALUATION (EXACT_MATCH, MINOR_DEVIATION, MAJOR_DEVIATION)
        ↓
PREDICTION VALIDATION (PredictionValidation: error = actual - predicted)
        ↓
MODEL PERFORMANCE HISTORY (ModelPerformanceSnapshot: MAE, RMSE, R², signed bias)
        ↓
RESEARCHER REVIEW & MODEL MONITORING (STABLE, WARNING, DEGRADED, CRITICAL)
```

## 2. Key Workflow Rules
1. Predictions are NEVER replaced or overwritten by actual results.
2. Actual synthesis parameters are recorded separately from predicted conditions.
3. Unit conversions (e.g. S/m $\rightarrow$ S/cm) are recorded with explicit conversion factors.
4. Target mismatch (e.g. conductivity vs band gap) results in immediate validation rejection.
