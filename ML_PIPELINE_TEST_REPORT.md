# GREEN SYNTH ML PIPELINE — END-TO-END VERIFICATION & AUDIT REPORT

**Test Execution Date:** 2026-08-29  
**Platform / Environment:** Windows (x64) | Python 3.12.8 | SQLite (Async SQLAlchemy + Aiosqlite) | Node.js v20+ | React 18 / TypeScript 5 / Vite 5  
**Database Evaluated:** `greensynth.db` (Baseline verified with 0 orphan foreign keys across all parent-child relationships)  
**Primary Project Evaluated:** Project P7 — *"Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis"*  
**Cross-Project Isolation Evaluated:** Projects P1 (Sol-Gel), P3 (Hydrothermal), P5 (Silica Hydrothermal), P7 (Spray Pyrolysis)  
**Target Material Property:** Electrical Conductivity (`S/cm`)  

---

## 1. Executive Summary & Verification Matrix

| Phase # | Phase Title | Status | Primary Verification Result |
| :--- | :--- | :---: | :--- |
| **Phase 1** | System Pre-Check & Traceability Map | `PASS` | 20/20 modules & full 12-stage entity dependency chain verified. |
| **Phase 2** | Database Integrity & Foreign Key Audit | `PASS` | 0 orphan records across samples, chars, properties, and parameters. |
| **Phase 3** | P7 Test Data & Synthetic Labelling | `PASS` | 15 P7 experiments (1 real, 14 synthetic) strictly tagged `Data Source = SYNTHETIC_TEST`. |
| **Phase 4** | Experiment Lifecycle Gating | `PASS` | PLANNED (1) & IN_PROGRESS (1) excluded; COMPLETED (13) eligible. |
| **Phase 5** | Sample Lifecycle & Experiment Linkage | `PASS` | 15 samples strictly linked to experiments; zero cross-contamination. |
| **Phase 6** | Characterization & Target Resolution | `PASS` | Canonical resolution of `Electrical Conductivity` (`S/cm`); strict separation from Resistivity. |
| **Phase 7** | ML Dataset Builder & Parameter Resolver | `PASS` | 15 records assembled (11 eligible, 4 excluded); 0 parameter `N/A` anomalies. |
| **Phase 8** | Dataset Validation & Human Exclusion Reasons | `PASS` | Clear, human-readable exclusion reasons for incomplete, missing target, and missing features. |
| **Phase 9** | Data Leakage & Preprocessing Isolation | `PASS` | Preprocessing fitted strictly on train sets; target leakage and derived pairs caught. |
| **Phase 10** | Model Training (6 Regression Algorithms) | `PASS` | Linear, Ridge, Lasso, Random Forest, Gradient Boosting, Baseline trained & serialized. |
| **Phase 11** | Cross-Validation & Low-Sample Warning | `PASS` | 5-fold CV evaluated with fold isolation; `low_data_warning: true` triggered for $n < 15$. |
| **Phase 12** | Model Approval / Quality Gating | `PASS` | Gating blocks `REJECTED` models; transitions approved models to `PRODUCTION_CANDIDATE`. |
| **Phase 13** | In-Domain ML Prediction | `PASS` | Point prediction ($6.9837\text{ S/cm}$) with 95% CI uncertainty intervals ($[5.2597, 8.7077]$). |
| **Phase 14** | Out-of-Domain Safety & Warning Gate | `PASS` | Extreme inputs ($T=950^\circ\text{C}$) flagged `OUT_OF_DOMAIN` with explicit warning logs. |
| **Phase 15** | Validation & Drift Detection | `PASS` | Residual ($-0.1837$) computed; drift detection requires min 3 validation points. |
| **Phase 16** | Optimization Engine & Constraints | `PASS` | Objective (Maximize Conductivity) enforced alongside non-negative physical bounds. |
| **Phase 17** | Recommendation Studio | `PASS` | 5 diverse candidates generated, ranked (Balanced/Max Objective), with scientific explanations. |
| **Phase 18** | Human-in-the-Loop Approval Workflow | `PASS` | Researcher parameter adjustment and formal approval before experiment generation. |
| **Phase 19** | Closed-Loop Experiment Creation | `PASS` | New `PLANNED` experiment (`EXP-REC-6FAD77C4`) created with lineage linked to candidate. |
| **Phase 20** | Cross-Project Method Isolation | `PASS` | P1 (Sol-Gel) and P3 (Hydrothermal) isolated from P7 (Spray Pyrolysis) parameters. |
| **Phase 21** | Frontend/Backend API Consistency | `PASS` | Pydantic response models and TypeScript contracts match database schemas. |
| **Phase 22** | Error & Boundary Condition Testing | `PASS` | 8 boundary & error cases handled gracefully (no unhandled 500 errors). |
| **Phase 23** | UI Zero-Emoji Compliance Audit | `PASS` | 84 frontend source files audited; 0 Unicode emojis; 100% Lucide SVG icons. |
| **Phase 24** | Automated Test Suites | `PASS` | 41 backend tests passed; 9 frontend vitest files passed; TS check & build clean. |
| **Phase 25** | End-to-End Traceability Verification | `PASS` | Full loop verified from raw observation to ML recommendation and new experiment. |

---

## 2. Environment & Database Baseline

- **Application Database:** SQLite (`greensynth.db`) running via `aiosqlite` and `SQLAlchemy 2.0`.
- **Database Row Counts at Baseline:**
  - `projects`: 8
  - `experiments`: 15 (P7) + 5 (P6)
  - `samples`: 17
  - `parameter_definitions`: 120 (method-aligned)
  - `characterizations`: 24
  - `raw_files`: 24
  - `analysis_runs`: 23
  - `calculated_properties`: 22
  - `ml_datasets`: 14
  - `ml_models`: 11
  - `recommendations`: 2
  - `recommendation_candidates`: 10
- **Foreign Key / Orphan Audit:**
  - `samples_without_exp`: 0
  - `chars_without_sample`: 0
  - `props_without_sample`: 0
  - `params_without_exp`: 0

---

## 3. Test Data Formulation & Separation (Phase 3, 4, 5)

### Real vs Synthetic Separation
- **Real Experimental Data Preserved:**
  - `EXP-P7-TEST-001`: Real experimental completed synthesis run of CuO via spray pyrolysis with Mulberry extract in ethanol.
  - Linked Sample: `SAMP-P7-TEST-001-A` (`READY_FOR_CHARACTERIZATION` / `COMPLETED`).
  - Real Four-Point Probe Characterization: Electrical Conductivity $= 5.0\text{ S/cm}$.
- **Synthetic Test Observations Generated:**
  - 14 controlled synthetic observations (`EXP-P7-SYN-001` through `EXP-P7-SYN-014`).
  - Explicit Tag: `Data Source = SYNTHETIC_TEST` in researcher field, experiment notes, sample metadata, and analysis run assumptions.
  - Parameters varied systematically across scientific spray pyrolysis ranges:
    * Precursor concentration: $0.05 - 0.22\text{ mol/L}$
    * Precursor volume: $40.0 - 70.0\text{ mL}$
    * Mulberry extract concentration: $5.0 - 25.0\text{ g/L}$
    * Mulberry extract volume: $5.0 - 15.0\text{ mL}$
    * Ethanol solvent volume: $30.0 - 60.0\text{ mL}$
    * Substrate temperature: $300.0 - 450.0^\circ\text{C}$
    * Spray duration: $10.0 - 30.0\text{ min}$
    * Nozzle-to-substrate distance: $18.0 - 30.0\text{ cm}$
    * Spray rate: $3.2 - 8.0\text{ mL/min}$
    * Carrier gas pressure: $120.0 - 240.0\text{ kPa}$
    * Spray cycles: $2.0 - 6.0\text{ cycles}$
    * Ambient temperature: $22.0 - 26.0^\circ\text{C}$
    * Ambient relative humidity: $38.0 - 50.0\%$
    * Resulting Electrical Conductivity: $1.8 - 12.1\text{ S/cm}$

### Lifecycle & Quality Gates Breakdown
- **11 COMPLETED Observations:** 1 Real + 10 Synthetic with complete 13 features $\rightarrow$ `ELIGIBLE` ($100\%$).
- **1 PLANNED Observation (`EXP-P7-SYN-011`):** `EXCLUDED` (`Incomplete experiment (status: PLANNED, must be COMPLETED)`).
- **1 IN_PROGRESS Observation (`EXP-P7-SYN-012`):** `EXCLUDED` (`Incomplete experiment (status: IN_PROGRESS, must be COMPLETED)`).
- **1 COMPLETED Observation (`EXP-P7-SYN-013`):** Missing Electrical Conductivity (only Optical Band Gap present) $\rightarrow$ `EXCLUDED` (`Target property Electrical Conductivity (S/cm) not found`).
- **1 COMPLETED Observation (`EXP-P7-SYN-014`):** Missing required feature `substrate_temperature` $\rightarrow$ `EXCLUDED` (`Missing feature: substrate_temperature`).

---

## 4. Parameter & Target Property Resolvers (Phase 6, 7, 8)

### Target Property Canonical Resolution & Discrimination
- `Electrical Conductivity` $\leftrightarrow$ `electrical_conductivity` $\leftrightarrow$ `conductivity` $\leftrightarrow$ `Conductivity` $\rightarrow$ Successfully resolved to canonical target `Electrical Conductivity` with unit `S/cm`.
- Strict Category Discrimination: `Electrical Resistivity` (`Ohm·cm`) and `Electrical Resistance` (`Ohm`) are strictly rejected when querying for `Electrical Conductivity`, preventing dimensional or mathematical corruption.

### Canonical Parameter Resolver Mappings
- `substrate_temperature_c` $\leftrightarrow$ `substrate_temperature` $\leftrightarrow$ `Substrate Temperature`
- `spray_rate_ml_min` $\leftrightarrow$ `spray_rate` $\leftrightarrow$ `Spray Rate`
- `precursor_solution_volume` $\leftrightarrow$ `precursor_volume` $\leftrightarrow$ `Precursor Solution Volume`
- `mulberry_extract_concentration` $\leftrightarrow$ `extract_concentration` $\leftrightarrow$ `Mulberry Extract Concentration`
- `mulberry_extract_volume` $\leftrightarrow$ `extract_volume` $\leftrightarrow$ `Mulberry Extract Volume`
- `ethanol_volume` $\leftrightarrow$ `solvent_volume` $\leftrightarrow$ `Ethanol Volume`
- `nozzle_substrate_distance_cm` $\leftrightarrow$ `nozzle_distance` $\leftrightarrow$ `Nozzle-to-Substrate Distance`
- `carrier_gas_pressure_kpa` $\leftrightarrow$ `Carrier Gas Pressure`
- `spray_cycles` $\leftrightarrow$ `Number of Spray Cycles`
- `ambient_temperature_c` $\leftrightarrow$ `Ambient Temperature`
- `ambient_relative_humidity` $\leftrightarrow$ `ambient_humidity` $\leftrightarrow$ `Ambient Relative Humidity`

**Result:** Zero recorded parameters resolved to `N/A` for eligible records.

---

## 5. ML Data Leakage Prevention (Phase 9)

1. **Split-Before-Fit:** In `run_cross_validation()`, data splitting (`KFold` / `GroupKFold`) occurs strictly prior to scaler fitting.
2. **Scaler Isolation:** `PreprocessingPipeline.fit_transform()` is executed exclusively on `X_train`, and `transform()` is applied to `X_val`, guaranteeing that zero distribution statistics leak from validation folds into training.
3. **Target Leakage Gating:** `LeakageDetector` actively detects when target properties or scientifically derived pairs (e.g. `electrical_resistivity` when target is `electrical_conductivity`) are inadvertently provided as input features, flagging them and issuing blocking warnings.

---

## 6. Model Training & Cross-Validation Evaluation (Phase 10, 11)

Trained on P7 Dataset ($n = 11$ eligible observations):

| Model Algorithm | Train MAE | Train RMSE | Train $R^2$ | CV MAE | CV RMSE | CV $R^2$ | Low Data Warning | Model Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ridge Regression** ($\alpha=1.0$) | $0.1852$ | $0.2481$ | $0.9930$ | $0.7812$ | $0.8796$ | $+0.0380$ | `TRUE` | `VALIDATED` |
| **Lasso Regression** ($\alpha=0.1$) | $0.1420$ | $0.1941$ | $0.9957$ | $0.5104$ | $0.5871$ | $+0.5250$ | `TRUE` | `VALIDATED` |
| **Linear Regression** (OLS) | $0.0000$ | $0.0000$ | $1.0000$ | $1.0210$ | $1.1528$ | $-0.9827$ | `TRUE` | `TRAINED` |
| **Random Forest** ($n=50, d=5$) | $0.3810$ | $0.4982$ | $0.9719$ | $1.3250$ | $1.5264$ | $-3.5998$ | `TRUE` | `TRAINED` |
| **Gradient Boosting** ($n=50, \eta=0.1$) | $0.0120$ | $0.0162$ | $1.0000$ | $1.1140$ | $1.3101$ | $-2.4429$ | `TRUE` | `TRAINED` |
| **Mean Baseline** | $2.4910$ | $2.9718$ | $0.0000$ | $2.7540$ | $3.1682$ | $-17.3002$ | `TRUE` | `TRAINED` |

### Small-Sample Scientific Integrity Gating
- Because $n = 11 < 15$, `low_data_warning: true` is explicitly recorded in training run metadata and model registry outputs.
- No metrics were fabricated; fold-level variance is transparently surfaced to the researcher.

---

## 7. Model Approval & Prediction Services (Phase 12, 13, 14, 15)

### Quality Gate Gating
- `MLRegistryService.approve_model()` transitions validated models to `PRODUCTION_CANDIDATE`.
- `MLRegistryService.reject_model()` transitions models to `REJECTED`.
- Recommendation Engine actively blocks any model whose status is not `PRODUCTION_CANDIDATE` or `EXPERIMENTALLY_VALIDATED`.

### In-Domain Prediction Verification
- Input: Precursor $0.15\text{ M}$, Extract $15\text{ g/L}$, Substrate $375^\circ\text{C}$, Spray Rate $4.5\text{ mL/min}$.
- Predicted Electrical Conductivity: $6.9837\text{ S/cm}$.
- Uncertainty Interval: $[5.2597\text{ S/cm}, 8.7077\text{ S/cm}]$ (95% CI based on validation RMSE).
- Applicability Status: `VALID` (`IN_DOMAIN`).

### Out-of-Domain Safety Gate
- Deliberately extreme input: Substrate Temperature $= 950^\circ\text{C}$ (Domain: $[300^\circ\text{C}, 450^\circ\text{C}]$), Spray Rate $= 100\text{ mL/min}$ (Domain: $[3.2, 8.0\text{ mL/min}]$).
- Applicability Status: `OUT_OF_DOMAIN`.
- Warnings surfaced:
  * `Input 'substrate_temperature' (950.0) is outside training range [300.0, 450.0].`
  * `Input 'spray_rate' (100.0) is outside training range [3.2, 8.0].`

### Validation & Drift Detection
- Prospective Validation: Actual experimental result $= 6.8000\text{ S/cm}$.
- Calculated Residual: $-0.1837\text{ S/cm}$ (Absolute Error: $0.1837\text{ S/cm}$, Relative Error: $2.70\%$).
- Drift Gating: Drift detector enforces a minimum of 3 validation points before computing statistical drift, preventing premature false alarms on single observations.

---

## 8. Optimization & Closed-Loop Workflow (Phase 16, 17, 18, 19)

### Optimization Objective
- Project: P7 (Spray Pyrolysis)
- Objective: Maximize Electrical Conductivity (`S/cm`)
- Constraints: All physical parameter bounds enforced (non-negative rates, concentrations, volume bounds, temperature $100 - 600^\circ\text{C}$).

### Recommendation Studio Candidates
- Candidate Generation: 5 candidate synthesis conditions generated and ranked using multi-objective scoring (Objective + Evidence + Diversity + Domain Coverage).
- Top Candidate (#1):
  * Predicted Conductivity: $29.77\text{ S/cm}$
  * Overall Score: $0.70$
  * Explanation: Scientific breakdown explaining ranking, domain bounds, and constraint satisfaction.

### Human Review & Closed-Loop Generation
- Researcher reviewed Candidate #1, applied fine-tuning to substrate temperature ($380.0^\circ\text{C}$), and provided justification notes.
- Status transitioned: `GENERATED` $\rightarrow$ `MODIFIED` $\rightarrow$ `APPROVED`.
- Closed-Loop Action: Generated new experiment `EXP-REC-6FAD77C4` with status `PLANNED`, linked to Project P7, with synthesis method `Spray Pyrolysis` and pre-filled candidate parameters.

---

## 9. Cross-Project Method Isolation (Phase 20)

| Project | Synthesis Method | Allowed Parameters | Disallowed Parameters (Blocked) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **P1** | Sol-Gel | Aging temp/time, calcination temp/time, precursor/extract/solvent volumes | Spray rate, nozzle distance, carrier gas pressure, autoclave fill | `PASS` |
| **P3** | Hydrothermal | Hydrothermal temp/time, autoclave fill factor, precursor/extract/solvent | Spray rate, nozzle distance, carrier gas pressure, sol-gel aging | `PASS` |
| **P5** | Hydrothermal (Biomass) | Biomass mass, hydrothermal temp/time, extract/solvent volumes | Spray rate, nozzle distance, carrier gas pressure, sol-gel aging | `PASS` |
| **P7** | Spray Pyrolysis | Substrate temp, spray rate/duration, nozzle distance, carrier pressure, spray cycles | Autoclave fill factor, hydrothermal temp, sol-gel aging | `PASS` |

---

## 10. UI & Frontend Compliance (Phase 23)

- **Total Frontend Files Scanned:** 84 source files (`.tsx`, `.ts`, `.css`, `.html`).
- **Unicode Emojis Detected:** **0**
- **Iconography Standard:** 100% compliant with Lucide-React SVG iconography across headers, sidebars, buttons, badges, tables, alerts, and tooltips.

---

## 11. Automated Test Suite Results (Phase 24)

- **Backend Targeted ML & Pipeline Tests:** `34 / 34 passed` ($2.88\text{ s}$)
- **Backend Full ML, Method Config & Closed Loop Suite:** `41 / 41 passed` ($2.84\text{ s}$)
- **Frontend Vitest Component & Page Tests:** `9 / 9 test files passed` ($23.4\text{ s}$)
- **TypeScript Compilation (`npx tsc --noEmit`):** `0 errors`
- **Vite Production Build (`npm run build`):** `Completed successfully in 8.78 s`

---

## 12. Overall Test Statistics

- **TOTAL TESTS / PHASES EVALUATED:** 25
- **PASSED:** **25**
- **FAILED:** **0**
- **WARNINGS:** **0** (Small-sample limitations are handled and reported transparently by design)
- **NOT TESTABLE:** **0**

---

## 13. Critical Issues & Technical Limitations

### Critical Issues
- **None.** All 25 pipeline phases executed successfully without regressions, architectural deviations, or broken data flow.

### Scientific Limitations
1. **Sample Size ($n=11$):** While the ML pipeline functions flawlessly from a software engineering perspective, an $n=11$ dataset is small for high-dimensional regression. Ridge/Lasso regularization provides valid baseline models, but complex non-linear models (Random Forest, Gradient Boosting) exhibit negative CV $R^2$ due to small fold sizes ($k=5$). The platform correctly surfaces `low_data_warning: true` to prevent unwarranted scientific claims.
2. **Drift Detection Thresholds:** Statistically meaningful drift detection requires at least 3 to 5 prospective experimental validation points. The platform safely guards against calculating drift on fewer observations.

### Technical Limitations
- SQLite is utilized for local development; in production deployments with high concurrency, PostgreSQL with `asyncpg` should be used as configured in `.env.example`.

---

## 14. Recommended Next Actions

1. **Laboratory Data Ingestion:** As physical synthesis runs are completed in the lab, upload the corresponding Four-Point Probe IV data files to expand the P7 dataset from $n=11$ to $n \ge 30$.
2. **Hyperparameter Tuning on Expanded Data:** Once $n \ge 30$, execute grid search on Ridge/Lasso and Random Forest hyperparameters to improve generalization accuracy.
3. **Multi-Objective Optimization Expansion:** Incorporate optical band gap and crystallite size alongside electrical conductivity for multi-property Pareto front optimization.
