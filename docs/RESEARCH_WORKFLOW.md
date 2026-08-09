# GreenSynth Analytics — 17-Stage Closed-Loop Research Workflow

```
1. CREATE PROJECT CONFIGURATION
        ↓
2. DEFINE SYNTHESIS PARAMETERS
        ↓
3. CREATE EXPERIMENT
        ↓
4. REGISTER PHYSICAL SAMPLE
        ↓
5. UPLOAD RAW CHARACTERIZATION FILES (SHA-256 Checksum)
        ↓
6. RUN SCIENTIFIC CALCULATIONS (XRD / UV-Vis / Electrical)
        ↓
7. CALCULATED PROPERTY DERIVATION (Bandgap, Size, Conductivity)
        ↓
8. STATISTICAL ANALYSIS & DOE REVIEW
        ↓
9. BUILD VERSIONED DATASET (V1 -> V2)
        ↓
10. TRAIN & VALIDATE ML MODEL (K-Fold CV, Domain Bounds)
        ↓
11. MODEL APPROVAL GATE (Approved / Retired)
        ↓
12. CONFIGURE OPTIMIZATION OBJECTIVES & CONSTRAINTS
        ↓
13. GENERATE & RANK PROMISING CANDIDATES (Exploitation vs Exploration)
        ↓
14. RESEARCHER CONVERTS CANDIDATE TO PLANNED EXPERIMENT
        ↓
15. PHYSICAL LABORATORY SYNTHESIS & MEASUREMENT
        ↓
16. PREDICTION VS ACTUAL ERROR EVALUATION (Validation Loop)
        ↓
17. MODEL PERFORMANCE SNAPSHOT & DRIFT MONITORING
```

## Stage Rules & Integrity Controls
- **Data Immortality**: Predictions, models, datasets, and raw files are never overwritten.
- **Human-in-the-Loop**: Candidate conditions are recommendations for researcher evaluation, never automatic lab control.
- **Model Gate**: RETIRED or CRITICAL models are automatically blocked from optimization.
- **Validation Evaluation**: Predictions are compared against physical measurements after synthesis to record signed error, absolute error, relative error, and interval coverage.
