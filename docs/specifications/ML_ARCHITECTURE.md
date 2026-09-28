# Phase 16: Machine Learning Prediction & Validation Architecture

## 1. Core Architectural Diagram
```
VALIDATED EXPERIMENTAL DATA
        ↓
DATASET VERSION (V1 -> V2)
        ↓
ML READINESS CHECK (MLReadinessValidator)
        ↓
FEATURE & TARGET SELECTION
        ↓
TRAIN / VALIDATION / TEST SPLIT
        ↓
PREPROCESSING PIPELINE (StandardScaler on Train only)
        ↓
MODEL TRAINING (Linear, Ridge, Lasso, RF, Gradient Boosting)
        ↓
CROSS-VALIDATION & OVERFITTING DETECTION
        ↓
MODEL COMPARISON & SELECTION
        ↓
MODEL REGISTRY (SHA256 Artifact Checksum & Metadata)
        ↓
RESEARCHER REVIEW & APPROVAL (TRAINED -> VALIDATED -> APPROVED)
        ↓
PREDICTION ENGINE (Feature Range & Training Distance Check)
        ↓
LABORATORY EXPERIMENT
        ↓
ACTUAL MEASUREMENT RECORDING
        ↓
PREDICTION VALIDATION (PredictionValidation)
```

## 2. Scientific Principles
- **Predictions are NOT measurements**: Predictions are labeled `PREDICTED` and never replace `MEASURED` laboratory data.
- **Interpretable Models**: Baseline models include Linear, Ridge, Lasso, Random Forest, and Gradient Boosting.
- **Data Leakage Isolation**: Preprocessing and scalers are fitted strictly on Training data.
- **Reproducibility**: All training runs record `random_seed`, library versions, and SHA256 checksums.
