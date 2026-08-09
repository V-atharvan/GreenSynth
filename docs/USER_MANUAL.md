# GreenSynth Analytics — Official Platform User Manual & Comprehensive Guide

**Software Version:** v1.0.0-research  
**Target Audience:** Scientific Researchers, Laboratory Personnel, Data Analysts, R&D Managers  
**System Type:** Data-Driven Experimental Analysis, Machine Learning, & Evidence-Based Optimization Platform for Green Synthesis of Semiconductor Materials

---

## OUTPUT 1: COMPLETE USER MANUAL

### Chapter 1: Introduction & Executive Overview
Welcome to **GreenSynth Analytics**, a specialized scientific computing platform built specifically for the green synthesis of semiconductor materials (such as Mulberry extract-mediated CuO thin films/nanoparticles via Spray Pyrolysis, Sol-Gel, and Hydrothermal deposition, as well as Rice husk-derived Silica/Silicon).

The system operates as a **digital laboratory notebook, automated scientific calculator, statistical modeling suite, machine learning engine, multi-objective optimizer, and prospective physical validation tracker**.

---

### Chapter 2: What is GreenSynth Analytics?
GreenSynth Analytics eliminates manual laboratory spreadsheet calculations, unverified property estimations, and disconnected data silos.

#### What Problem Does it Solve?
1. **Manual Calculation Errors**: Automatically derives crystallite size ($D$) via the Scherrer equation, optical band gap ($E_g$) via Tauc plot linear extrapolation, and electrical conductivity ($\sigma$) via Ohm’s Law linear regression.
2. **Data Tampering & Loss**: Calculates cryptographic SHA-256 checksums on all raw characterization file uploads (`.csv`), ensuring raw laboratory measurements remain 100% immutable and reproducible.
3. **Black-Box Machine Learning**: Enforces 5-Fold Cross Validation, Applicability Domain bounds checking (`IN_DOMAIN`, `NEAR_BOUNDARY`, `OUT_OF_DOMAIN`), and transparent multi-objective scoring for candidate experimental recommendations.
4. **Unvalidated ML Predictions**: Implements closed-loop prospective validation, comparing model predictions against actual physical laboratory measurements to record signed error, absolute error, relative error (%), interval coverage, and Model Health Snapshots.

---

### Chapter 3: Who Should Use It?
- **Laboratory Researchers**: To log synthesis conditions, store raw characterization spectra, and derive physical properties automatically.
- **Data Analysts & Statisticians**: To evaluate multi-sample correlations, OLS regression fits, One-Way ANOVA, and Q-Q residual diagnostics.
- **Machine Learning Engineers**: To build versioned training datasets (`v1.0`, `v2.0`), train regression models (Ridge, Random Forest, Gradient Boosting), and monitor model drift.
- **Research Directors**: To inspect project synthesis matrices across all 8 laboratory projects (`P1`–`P8`) and export formal PDF reports with cryptographic data provenance.

---

### Chapter 4: Overall Research Loop Workflow

```
   1. Select Project (P1–P8)
           │
           ▼
   2. Record Experiment & Synthesis Parameters
           │
           ▼
   3. Create Physical Sample Record
           │
           ▼
   4. [RESEARCHER PHYSICAL LAB ACTION] Perform Physical Synthesis
           │
           ▼
   5. Upload Raw Characterization Files (SHA-256 Checksum Verification)
           │
           ▼
   6. Execute Automated Scientific Analysis (XRD / UV-Vis / Electrical / FTIR / SEM)
           │
           ▼
   7. Review Calculated Scientific Properties
           │
           ▼
   8. Perform Multi-Sample Comparison & Statistical Diagnostics
           │
           ▼
   9. Build Versioned ML Dataset & Train Regression Model (5-Fold CV)
           │
           ▼
   10. Configure Multi-Objective Optimization & Generate Candidate Conditions
           │
           ▼
   11. Convert Candidate to PLANNED Experiment
           │
           ▼
   12. [RESEARCHER PHYSICAL LAB ACTION] Perform Physical Candidate Synthesis
           │
           ▼
   13. Record Prospective Validation (Predicted vs. Actual Error Evaluation)
           │
           ▼
   14. Log Model Health Snapshot & Export Formal PDF Scientific Report
```

---

### Chapter 5: Before You Start — Prerequisite Research Data

Before creating an experiment, assemble your target laboratory parameters:

| Parameter Name | Parameter Code | Unit | Valid Range | Example Value | Description |
|---|---|---|---|---|---|
| **Copper Precursor Salt** | `precursor_type` | Text | Catalog ENUM | `Copper Acetate` | Metallic precursor salt |
| **Precursor Concentration** | `precursor_concentration_mol_l` | mol/L | `0.01` to `2.0` | `0.1` | Concentration in solvent |
| **Extract Concentration** | `extract_concentration_g_l` | g/L | `1.0` to `100.0` | `10.0` | Phytochemical extract mass per volume |
| **Solvent Type** | `solvent_type` | Text | `Ethanol`, `Acetone` | `Ethanol` | Reaction solvent |
| **Substrate Temperature** | `substrate_temperature_c` | °C | `100` to `600` | `350` | Deposition hotplate/stage temperature |
| **Spray Rate** | `spray_rate_ml_min` | mL/min | `0.5` to `20.0` | `5.0` | Solution atomization flow rate |
| **Spray Duration** | `spray_duration_min` | min | `1` to `120` | `15` | Total spray time |
| **Nozzle Distance** | `nozzle_distance_cm` | cm | `5` to `50` | `20` | Nozzle to substrate distance |
| **Substrate Type** | `substrate_type` | Text | `Glass`, `Quartz`, `Silicon` | `Glass` | Thin film deposition substrate |

---

### Chapter 6: Dashboard Overview (`/`)
- **Header Overview**: Shows total Active Projects, Total Experiments, Total Samples, and Completed Experiments.
- **Experiments by Status**: Visual progress bars showing breakdown across `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`.
- **Recent Experiments Table**: Direct links to view active research experiments.
- **Quick Action Buttons**: Fast shortcuts to **Browse Projects**, **View Experiments**, and **View Samples**.

---

### Chapter 7: Multi-Project Research Matrix (`/projects`)
GreenSynth Analytics features a configuration-driven engine supporting 8 distinct laboratory research projects:

- **P1**: CuO + Mulberry + Ethanol + Sol-Gel
- **P2**: CuO + Mulberry + Acetone + Sol-Gel
- **P3**: CuO + Mulberry + Ethanol + Hydrothermal
- **P4**: CuO + Mulberry + Acetone + Hydrothermal
- **P5**: Silica/Silicon + Rice Husk + Mulberry + Ethanol + Hydrothermal
- **P6**: Silica/Silicon + Rice Husk + Mulberry + Acetone + Hydrothermal
- **P7**: CuO + Mulberry + Ethanol + Spray Pyrolysis (*MVP Reference*)
- **P8**: CuO + Mulberry + Acetone + Spray Pyrolysis

#### Property Comparability Checker Modal
Click **Check Property Comparability** on `/projects` to evaluate cross-project property comparability. The system evaluates whether properties between two projects can be compared directly (`COMPARABLE`), require caution (`COMPARABLE_WITH_WARNING`), or are scientifically invalid (`NOT_COMPARABLE`, e.g. CuO vs. Silica/Silicon).

---

### Chapter 8: Managing Experiments (`/experiments`)
1. Navigate to **Experiments** (`/experiments`).
2. Click **+ New Experiment**.
3. Select your target **Research Project** (e.g. Project 7).
4. Enter unique **Experiment Code** (e.g. `EXP-P7-007`).
5. Enter **Title**, **Researcher Name**, **Date**, and **Objective/Notes**.
6. Click **Save Experiment**.

---

### Chapter 9: Recording Synthesis Parameters
1. Open your created Experiment Detail page (`/experiments/:id`).
2. Click the **Synthesis Parameters** tab.
3. Input your recorded numerical parameter values.
4. Click **Save Parameters**. The values are validated against parameter definitions and stored permanently in `experiment_parameters`.

---

### Chapter 10: Creating & Managing Samples (`/samples`)
1. Open the **Samples** tab under Experiment Detail.
2. Click **+ Add Sample**.
3. Enter **Sample Code** (e.g. `SAMP-P7-007-A`), **Sample Name**, and **Substrate Type** (`Glass`).
4. Click **Create Sample**.

#### Sample Status Lifecycle:
- `PREPARED`: Physical specimen created in laboratory.
- `READY_FOR_CHARACTERIZATION`: Specimen transferred to analytical laboratory.
- `UNDER_ANALYSIS`: Characterization measurement in progress.
- `COMPLETED`: Measurement and scientific property derivation complete.

---

### Chapter 11: Laboratory Characterization Runs (`/samples/:id`)
1. Open the target Sample Detail page (`/samples/:id`).
2. Click **+ Add Characterization Run**.
3. Select **Technique** (`XRD`, `UV_VIS`, `ELECTRICAL`, `FTIR`, `SEM`).
4. Input Analyst Name, Instrument Name (e.g. *Rigaku Ultima IV*), Instrument Model, and Measurement Date.
5. Click **Create Characterization Record**.

---

### Chapter 12: Raw Data Upload & SHA-256 Checksum Verification
1. On the Characterization record card, click **Upload Raw File**.
2. Select your raw data file (e.g. `sample_data/P7_XRD_CuO.csv`).
3. Click **Upload File**.
4. The system calculates a cryptographic SHA-256 hash immediately.
5. If an identical file has already been uploaded in the system, a warning badge is displayed: *"An identical file already exists."*

---

### Chapter 13: XRD Analysis & Scherrer Crystallite Size Derivation

#### Input File Requirements:
- 2-Column CSV file containing $2\theta$ diffraction angle (degrees) and intensity counts.

#### Scientific Calculation:
Executes automated peak detection via Scipy signal processing (`find_peaks`) and applies the **Scherrer Equation**:
$$D = \frac{K \cdot \lambda}{\beta \cdot \cos\theta}$$
where $K = 0.9$ (shape factor), $\lambda = 0.15406\text{ nm}$ ($\text{Cu } K\alpha$), $\theta$ is the Bragg angle in radians, and $\beta$ is the Full Width at Half Maximum (FWHM) in radians.

#### How to Run:
1. Open sample detail with uploaded XRD file.
2. Click **Run Scientific Analysis**.
3. View interactive spectrum plot, detected peak table ($2\theta$, Intensity, FWHM), and derived **Crystallite Size $D$ (nm)** `[CALCULATED DATA]`.

---

### Chapter 14: UV-Vis Spectroscopy & Tauc Plot Band Gap Analysis

#### Input File Requirements:
- 2-Column CSV file containing Wavelength $\lambda$ (nm) and Absorbance ($A$).

#### Scientific Calculation:
Applies baseline correction, computes photon energy $h\nu = \frac{1240.8}{\lambda}$, transforms data using the **Tauc Relation**:
$$(\alpha \cdot h\nu)^{1/\gamma} \text{ vs. } h\nu$$
where $\gamma = 0.5$ for Direct Allowed optical transitions in CuO semiconductors. Extrapolates the linear slope region to $(\alpha h\nu)^2 = 0$ to derive the **Optical Band Gap ($E_g$) in eV**.

#### How to Run:
1. Open sample detail with uploaded UV-Vis file.
2. Click **Run Scientific Analysis**.
3. View interactive Tauc Plot chart and derived **Optical Band Gap $E_g$ (eV)** `[CALCULATED DATA]`.

---

### Chapter 15: Electrical I-V Measurement & Conductivity Fit

#### Input File Requirements:
- 2-Column CSV file containing Voltage (V) and Current (A).

#### Scientific Calculation:
Applies Ohm’s Law linear regression fitting ($I = \frac{V}{R}$) to derive Resistance $R$ ($\Omega$). Combines sample geometry (film thickness $t$, width $w$, length $L$) to compute Resistivity $\rho$ and **Electrical Conductivity $\sigma$**:
$$\rho = R \cdot \frac{w \cdot t}{L} \quad (\Omega\cdot\text{cm})$$
$$\sigma = \frac{1}{\rho} \quad (\text{S/cm})$$

#### How to Run:
1. Open sample detail with uploaded I-V file.
2. Ensure sample film thickness ($t$), length ($L$), and width ($w$) are entered.
3. Click **Run Scientific Analysis**.
4. View $I\text{--}V$ linear regression fit plot, $R^2$ fit score, and derived **Conductivity $\sigma$ (S/cm)** `[CALCULATED DATA]`.

---

### Chapter 16: FTIR Spectroscopy & Peak Annotation (`/samples/:id`)
- **Input File Requirements**: 2-Column CSV file containing Wavenumber ($\text{cm}^{-1}$) and Transmittance (%).
- **Automated Annotation**: Software-assisted peak annotation matching functional groups (e.g., $530\text{ cm}^{-1}$ Cu-O stretching vibration).

---

### Chapter 17: SEM Image Analysis & Scale Bar Calibration (`/samples/:id`)
- **Supported Formats**: PNG, JPG image upload.
- **Interactive Calibration**: Pixel-to-micron scale bar mapping for grain size measurement.

---

### Chapter 18: Sample Comparison (`/comparison`)
1. Navigate to **Sample Comparison** (`/comparison`).
2. Select your target Research Project.
3. View **Multi-Sample Comparison Table** comparing precursor concentration, substrate temperature, crystallite size, band gap, and conductivity side-by-side.
4. Inspect the **Data Quality Report** alerting missing variables.

---

### Chapter 19: Statistical Evidence Studio (`/statistics`)
1. Navigate to **Statistical Evidence** (`/statistics`).
2. Select Independent ($X$) and Dependent ($Y$) variables.
3. Click **Run Analysis** to execute:
   - **Pearson Correlation ($r$) & Spearman ($\rho$)**
   - **Ordinary Least Squares (OLS) Regression ($R^2$, slope, $p$-value)**
   - **One-Way ANOVA ($F$-statistic, $p$-value)**
   - **Q-Q Residual Diagnostics Plot**

---

### Chapter 20: Design of Experiments (DOE) (`/doe`)
1. Navigate to **Design of Experiments** (`/doe`).
2. Select DOE Type: **Full Factorial**, **Fractional Factorial**, **Central Composite Design (CCD)**, or **Box-Behnken**.
3. Set factors (Substrate Temperature, Spray Rate, Precursor Concentration) and bounds.
4. Input random seed for 100% reproducible run order matrix generation.
5. Click **Generate Design Matrix**.

---

### Chapter 21: Machine Learning Center (`/ml`)
The ML Center provides an end-to-end framework for dataset building, model training, cross-validation, prediction, and domain bounds checking.

---

### Chapter 22: Building Versioned ML Datasets (`/ml/datasets/new`)
1. Open **Machine Learning** $\rightarrow$ **Build Dataset**.
2. Select target Research Project.
3. System runs **Target Leakage Check** to ensure target property is excluded from input feature list.
4. Select input feature columns (Substrate Temperature, Spray Rate, Precursor Concentration).
5. Select target property (e.g. `conductivity_s_cm`).
6. Click **Build Versioned Dataset** (creates immutable version `v1.0`).

---

### Chapter 23: Training ML Models (`/ml/training`)
1. Open **ML Model Training** (`/ml/training`).
2. Select Dataset `v1.0`.
3. Choose ML Regressor:
   - **Baseline Dummy Regressor** (Mean benchmark)
   - **Ridge Linear Regression** (L2 Regularized)
   - **Random Forest Regressor** (Ensemble trees)
   - **Gradient Boosting Regressor** (Boosted decision trees)
4. Set 5-Fold Cross Validation.
5. Click **Train Model**.
6. System displays $R^2$, RMSE, MAE metrics, and parity plot ($y_\text{act}$ vs $y_\text{pred}$). Approved models are saved into the Model Registry with status `APPROVED`.

---

### Chapter 24: Making Property Predictions (`/ml/predict`)
1. Open **ML Prediction** (`/ml/predict`).
2. Select an `APPROVED` ML model.
3. Input candidate synthesis parameter values.
4. Click **Predict Property**.
5. System returns:
   - **Predicted Value** `[PREDICTED DATA]`
   - **95% Confidence Interval Bounds** `[lower_bound, upper_bound]`
   - **Applicability Domain Status**: `IN_DOMAIN`, `NEAR_BOUNDARY`, or `OUT_OF_DOMAIN`.

---

### Chapter 25: Applicability Domain Bounds
The applicability domain checks whether candidate input parameters lie within the minimum and maximum feature space used during model training:
- `IN_DOMAIN`: All inputs lie strictly within training feature bounds. High prediction confidence.
- `NEAR_BOUNDARY`: Inputs are within 5% of training feature limits. Moderate prediction confidence.
- `OUT_OF_DOMAIN`: Inputs exceed training feature range. Caution warning badge displayed.

---

### Chapter 26: Multi-Objective Experimental Optimization (`/optimization`)
1. Open **Experimental Optimization** (`/optimization`).
2. Select target property (`conductivity_s_cm`).
3. Set direction: `MAXIMIZE`, `MINIMIZE`, or `TARGET`.
4. Set weight (0.0 to 1.0) and parameter constraints.
5. Choose Search Engine: **Grid Search**, **Random Search (with seed)**, or **Model-Guided Search**.
6. Click **Run Candidate Generation**.
7. System generates and ranks candidates, categorizing them as **EXPLOITATION** (refining high-performing regions) or **EXPLORATION** (investigating under-sampled regions).

---

### Chapter 27: Candidate Selection & Candidate-to-Experiment Converter
1. Review the ranked candidate table on `/optimization`.
2. Inspect score breakdown and predicted properties `[RECOMMENDED DATA]`.
3. Click **Select Candidate**, then click **🔬 Create Experiment**.
4. The system automatically creates a new `PLANNED` experiment with the candidate parameter values populated into proposed conditions.

---

### Chapter 28: Closed-Loop Research Workflow (`/closed-loop`)
Displays the interactive 17-stage research loop status, tracking candidates converted to physical experiments and overall model promotion readiness.

---

### Chapter 29: Prospective Validation & Model Health (`/validation`)
1. Once the physical candidate experiment is synthesized and measured in the laboratory, open **Validation & Drift** (`/validation/experimental`).
2. Link the original predicted value against the actual measured physical value.
3. Click **Validate Prediction**.
4. The system calculates:
   - **Signed Error**: $y_\text{pred} - y_\text{act}$
   - **Absolute Error**: $|y_\text{pred} - y_\text{act}|$
   - **Relative Error (%)**: $\frac{|y_\text{pred} - y_\text{act}|}{y_\text{act}} \times 100$
   - **Interval Coverage**: `TRUE` if $y_\text{act} \in [\text{Lower Bound}, \text{Upper Bound}]$.
5. Click **Log Model Health Snapshot**. The system updates cumulative MAPE and records model status (`STABLE`, `WARNING`, `CRITICAL`).

---

### Chapter 30: Scientific PDF Report Generation & Data Export (`/reports`)
1. Open any Experiment Detail page (`/experiments/:id`).
2. Click **📄 Export PDF Report**.
3. The system generates and downloads a formal publication-grade ReportLab PDF (`Experiment_Report_EXP-P7-001.pdf`).

#### PDF Report Features:
- 14 Structured Sections (Cover, Project Config, Parameters, Samples, XRD, UV-Vis, Electrical, FTIR, SEM, Statistics, ML, Optimization, Validation, Provenance).
- Embedded Matplotlib spectrum plots and Tauc/IV regression charts.
- Explicit visual classification badges (`[MEASURED DATA]`, `[CALCULATED DATA]`, `[PREDICTED DATA]`, `[RECOMMENDED DATA]`, `[VALIDATED DATA]`).
- Cryptographic SHA-256 raw file provenance table.

---

### Chapter 31: Scientific Data Provenance & Integrity Block
Every scientific calculation and PDF report includes an immutable provenance block:
- **Raw File ID & Filename**
- **SHA-256 Cryptographic Checksum**
- **Analysis Run ID & Software Version (`1.0.0-research`)**
- **Processing Parameters & Timestamp**

---

### Chapter 32: System Status Reference Dictionary

| Entity | Status Name | Definition | Researcher Action Required |
|---|---|---|---|
| **Experiment** | `PLANNED` | Experiment created; parameters defined | Perform physical lab synthesis |
| **Experiment** | `IN_PROGRESS` | Synthesis currently under way | Complete lab trial |
| **Experiment** | `COMPLETED` | Synthesis & measurements finished | Review properties & export report |
| **Experiment** | `FAILED` | Synthesis trial failed in laboratory | Document failure notes |
| **Sample** | `PREPARED` | Specimen fabricated | Transfer to characterization lab |
| **Sample** | `READY_FOR_CHARACTERIZATION` | Specimen awaiting measurement | Conduct XRD/UV-Vis/Electrical measurement |
| **Sample** | `COMPLETED` | Characterization complete | Proceed to scientific analysis |
| **ML Model** | `TRAINED` | Model trained on versioned dataset | Perform cross-validation evaluation |
| **ML Model** | `APPROVED` | Model passed CV & domain checks | Enable for predictions & optimization |
| **ML Model** | `RETIRED` | Model performance degraded | Train updated model on Dataset v2 |
| **Model Health** | `STABLE` | Cumulative MAPE $< 10\%$ | Model safe for research use |
| **Model Health** | `WARNING` | Cumulative MAPE $10\text{--}20\%$ | Caution; collect validation samples |
| **Model Health** | `CRITICAL` | Cumulative MAPE $> 20\%$ | Model blocked from candidate optimization |

---

### Chapter 33: Error Handling & Troubleshooting Dictionary

| Symptom / Error Message | Root Cause | Resolution Step |
|---|---|---|
| `Request failed with status code 422` | API parameter type validation failure or route path parameter collision | Ensure backend server is running with updated router order in `main.py`. |
| `Cannot reach the server (ConnectionRefusedError)` | FastAPI Uvicorn backend server is not running on port 8000 | Start backend: `$env:PYTHONPATH="backend"; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| `An identical file already exists` | SHA-256 hash match detected on uploaded raw file | File is already archived intact. Use existing raw file record. |
| `XRD analysis error: missing columns` | Uploaded CSV lacks 2-column format (Angle, Intensity) | Ensure raw XRD file contains 2 numeric columns without textual headers. |
| `Optimization blocked: Model is RETIRED` | Selected ML model failed health check | Select an `APPROVED` model version in Optimization Studio. |

---

### Chapter 34: Common Researcher Mistakes to Avoid
1. ❌ **Confusing Predicted Values with Measured Values**: Predictions are estimates from ML models; physical measurements require physical lab trial.
2. ❌ **Extrapolating Out-of-Domain Predictions**: Pay attention to the `OUT_OF_DOMAIN` badge when evaluating candidate predictions.
3. ❌ **Assuming Correlation Equals Causation**: Statistical correlation reports observed relationships in data, not confirmed physical mechanisms.
4. ❌ **Silently Filling Missing Data**: Never fabricate placeholder values for unmeasured parameters.

---

### Chapter 35: Complete End-to-End Example Workflow (Project 7)

```
[STEP 1: SOFTWARE ACTION] Create Experiment EXP-P7-007 on /experiments
                     ↓
[STEP 2: SOFTWARE ACTION] Save Parameters: Temp=350°C, Rate=5mL/min, Extract=10g/L
                     ↓
[STEP 3: SOFTWARE ACTION] Create Sample SAMP-P7-007-A
                     ↓
[STEP 4: RESEARCHER PHYSICAL LAB ACTION] Synthesize CuO thin film via Spray Pyrolysis
                     ↓
[STEP 5: RESEARCHER PHYSICAL LAB ACTION] Measure XRD & UV-Vis spectra in lab
                     ↓
[STEP 6: SOFTWARE ACTION] Upload P7_XRD_CuO.csv & P7_UVVIS_CuO.csv (SHA-256 verified)
                     ↓
[STEP 7: SOFTWARE ACTION] Run Scientific Analysis: Derives D=22.4nm, Eg=1.45eV
                     ↓
[STEP 8: SOFTWARE ACTION] Train Random Forest ML Model on Dataset v1.0 (R²=0.91)
                     ↓
[STEP 9: SOFTWARE ACTION] Run Experimental Optimization (MAXIMIZE conductivity)
                     ↓
[STEP 10: SOFTWARE ACTION] Select Candidate #1 (Temp=380°C, Rate=6mL/min) & Click Create Experiment
                     ↓
[STEP 11: RESEARCHER PHYSICAL LAB ACTION] Perform Physical Candidate Synthesis in Lab
                     ↓
[STEP 12: SOFTWARE ACTION] Upload Measured Conductivity (4.95 S/cm) vs Predicted (5.12 S/cm)
                     ↓
[STEP 13: SOFTWARE ACTION] Record Validation (Error: 3.32%) & Export PDF Report
```

---

### Chapter 36: Current Application Limitations
- **UI Login Wall**: System defaults to open dashboard access without login wall (Backend `User` ORM model exists; UI login page planned for multi-tenant deployment).
- **In-Memory Chart Rendering**: PDF charts use Matplotlib in-memory rendering; large batch exports should limit figure resolution for speed.

---

### Chapter 37: Glossary of Terms
- **Band Gap ($E_g$)**: Energy difference (in eV) between valence and conduction bands in semiconductor CuO.
- **Crystallite Size ($D$)**: Average size of coherent crystalline domains calculated via the Scherrer equation.
- **FWHM**: Full Width at Half Maximum of a diffraction peak (in radians).
- **Tauc Plot**: Optical absorption transformation $(\alpha h\nu)^{1/\gamma}$ vs $h\nu$ used to measure semiconductor band gaps.
- **Conductivity ($\sigma$)**: Electrical charge transport capability measured in S/cm ($1/\rho$).
- **SHA-256**: Cryptographic 256-bit hash algorithm ensuring raw file immutability.

---

### Chapter 38: Quick Reference Guide
- **Launch Backend**: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Launch Frontend**: `npm run dev` (running on `http://localhost:5173`)
- **System Backup**: `python scripts/backup.py`
- **System Restore**: `python scripts/restore.py backups/greensynth_backup_YYYYMMDD_HHMMSS.zip`
- **Run Unit Tests**: `python -m pytest backend/tests/unit/ -v`

---

### Chapter 39: End-to-End Workflow Diagram

```
[PROJECT P1-P8] ──► [EXPERIMENT] ──► [SAMPLE] ──► [PHYSICAL LAB SYNTHESIS]
                                                          │
   [PDF REPORT] ◄── [VALIDATION & DRIFT] ◄── [RAW DATA UPLOAD (SHA-256)]
        ▲                                                 │
        │                                                 ▼
 [OPTIMIZATION] ◄── [ML PREDICTION] ◄── [ML MODEL] ◄── [SCIENTIFIC ANALYSIS]
```

---

### Chapter 40: Documentation Audit Summary
- **Routes Inspected**: 20 frontend routes / 18 backend API routers.
- **Workflows Verified**: 17 closed-loop research stages verified.
- **Implemented Modules**: 100% core scientific calculation engines, SHA-256 verification, ML training, optimization, validation, and PDF reporting.
- **Status**: **RESEARCH-READY** (v1.0.0-research).

---

## OUTPUT 2: QUICK START GUIDE
### "Your First 30 Minutes with GreenSynth Analytics"

1. **Launch Platform**: Open browser at `http://localhost:5173`.
2. **Select Project**: Click **Projects** $\rightarrow$ select **`P7 — CuO Phytochemical Synthesis via Spray Pyrolysis`**.
3. **Create Experiment**: Click **+ New Experiment** $\rightarrow$ enter code `EXP-P7-001` $\rightarrow$ save.
4. **Enter Parameters**: In Synthesis Parameters tab, enter Substrate Temp = `350 °C`, Spray Rate = `5 mL/min`, Precursor Conc = `0.1 mol/L` $\rightarrow$ save.
5. **Create Sample**: In Samples tab, click **+ Add Sample** $\rightarrow$ enter `SAMP-P7-001-A` $\rightarrow$ create.
6. **Upload Sample Data**: Open `SAMP-P7-001-A` $\rightarrow$ click **Upload Raw File** $\rightarrow$ upload [sample_data/P7_XRD_CuO.csv](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/CRTD/sample_data/P7_XRD_CuO.csv) (Technique: `XRD`).
7. **Run Scientific Analysis**: Click **Run Scientific Analysis** $\rightarrow$ view Scherrer crystallite size ($D = 22.4\text{ nm}$).
8. **Export Scientific PDF Report**: Click **📄 Export PDF Report** to download your formal scientific PDF report!

---

## OUTPUT 3: COMPLETE WORKFLOW DIAGRAM

```
                       RESEARCHER PHYSICAL ACTION
                                   │
              (Perform physical synthesis in laboratory)
                                   │
                                   ▼
                       SOFTWARE SYSTEM ACTION
                                   │
              (Upload raw data CSV -> SHA-256 Hash check)
                                   │
                                   ▼
                       SCIENTIFIC DERIVATION
                                   │
         (Compute Crystallite Size D, Band Gap Eg, Conductivity σ)
                                   │
                                   ▼
                    MACHINE LEARNING & OPTIMIZATION
                                   │
          (Train Model -> Predict Property -> Rank Candidates)
                                   │
                                   ▼
                     CLOSED-LOOP VALIDATION & DRIFT
                                   │
         (Compare Predicted vs Actual -> Log Health Snapshot -> PDF Report)
```

---

## OUTPUT 4: SCREENSHOT PLAN

| Screenshot ID | Page / Route | UI State / Focus | Caption | Location in Manual |
|---|---|---|---|---|
| **Screenshot 1** | Dashboard (`/`) | Metric cards & status bars | "Research Dashboard overview showing project counters and recent experiments." | Chapter 6 |
| **Screenshot 2** | Projects (`/projects`) | 8-Project Synthesis Matrix | "Multi-Project Synthesis Matrix representing projects P1 to P8." | Chapter 7 |
| **Screenshot 3** | Experiment Detail (`/experiments/:id`) | Parameters table & PDF button | "Experiment Detail view displaying recorded synthesis parameters and PDF export action." | Chapter 8 & 9 |
| **Screenshot 4** | Sample Detail (`/samples/:id`) | Raw file upload card & analysis | "Sample Detail page with SHA-256 verified raw file upload card." | Chapter 11 & 12 |
| **Screenshot 5** | Sample Comparison (`/comparison`) | Provenance table & Data Quality alert | "Multi-Sample Comparison Table displaying measured, calculated, and missing values." | Chapter 18 |
| **Screenshot 6** | Optimization Studio (`/optimization`) | Candidate ranking table | "Experimental Optimization Studio showing ranked candidate conditions and candidate converter." | Chapter 26 & 27 |
| **Screenshot 7** | Validation Studio (`/validation`) | Error comparison card | "Prospective Validation Loop displaying predicted vs actual physical measurement error." | Chapter 29 |

---

## OUTPUT 5: FEATURE MATRIX

| Feature | UI Available | Backend Available | Status | Implementation Notes |
|---|---|---|---|---|
| **Multi-Project Platform (P1–P8)** | YES | YES | ✅ Fully Working | Shared method engines, catalogs, comparability checker |
| **Synthesis Parameter Engine** | YES | YES | ✅ Fully Working | Recorded parameter validation & `parameters_json` |
| **SHA-256 Checksum Integrity** | YES | YES | ✅ Fully Working | Cryptographic raw file hash verification & duplicate detection |
| **XRD Crystallite Size Derivation** | YES | YES | ✅ Fully Working | Scipy peak detection & Scherrer equation ($D$) |
| **UV-Vis Tauc Band Gap Derivation** | YES | YES | ✅ Fully Working | Baseline correction, Tauc relation & slope extrapolation ($E_g$) |
| **Electrical Conductivity Fit** | YES | YES | ✅ Fully Working | $I\text{--}V$ Ohm's Law regression fit ($\rho, \sigma$) |
| **Sample Comparison & Stats** | YES | YES | ✅ Fully Working | ANOVA, OLS regression, Pearson/Spearman, Q-Q plots |
| **DOE Design Matrix Generator** | YES | YES | ✅ Fully Working | Full/Fractional Factorial, CCD, Box-Behnken matrix |
| **ML Training & Registry** | YES | YES | ✅ Fully Working | 5-Fold CV, 4 regressors, dataset versioning, model gate |
| **Applicability Domain Checking** | YES | YES | ✅ Fully Working | Training feature min/max bounds evaluation |
| **Candidate Optimization Studio** | YES | YES | ✅ Fully Working | Multi-objective scoring, search space engine, candidate converter |
| **Prospective Error Validation** | YES | YES | ✅ Fully Working | Signed, absolute, relative error %, interval coverage, health log |
| **Scientific PDF Report Generator** | YES | YES | ✅ Fully Working | ReportLab engine, 14 sections, provenance & classification badges |
| **CLI Backup & Restore** | N/A | YES | ✅ Fully Working | Python scripts (`backup.py`, `restore.py`) with manifest SHA-256 check |

---

## OUTPUT 6: USER FLOW MATRIX

| Step | Researcher Action | Application Action | Input Data | Output Data | Next Step |
|---|---|---|---|---|---|
| **1. Select Project** | Opens `/projects` & selects project | Loads project matrix & definitions | Project Selection (`P7`) | Project configuration view | Create experiment |
| **2. Create Exp** | Clicks `+ New Experiment` | Creates experiment entity (`PLANNED`) | Code, Title, Researcher, Date | Experiment record created | Record parameters |
| **3. Set Params** | Inputs parameter values | Validates ranges & stores | Temp (`350°C`), Rate (`5mL/min`) | Saved parameters table | Create sample |
| **4. Create Sample** | Clicks `+ Add Sample` | Instantiates sample linked to Exp | Code (`SAMP-P7-001-A`), Substrate | Physical sample card | Perform lab synthesis |
| **5. Upload Data** | Uploads raw CSV file | Calculates SHA-256 & stores raw file | Raw `.csv` file | Verified file card `[RAW DATA]` | Run analysis |
| **6. Run Analysis** | Clicks `Run Analysis` | Derives physical property | Raw spectrum arrays | $D=22.4\text{nm}, E_g=1.45\text{eV}$ | Compare / ML |
| **7. Train Model** | Opens `/ml/training` & trains model | Executes 5-Fold CV & saves model | Versioned dataset `v1.0` | Trained model ($R^2=0.91$) | Run optimization |
| **8. Optimize** | Configures objective & runs search | Scores & ranks candidates | Target (`conductivity`), Direction | Ranked candidates `[RECOMMENDED]` | Convert candidate |
| **9. Convert Candidate** | Clicks `🔬 Create Experiment` | Instantiates planned experiment | Candidate ID | New `PLANNED` experiment | Perform lab trial |
| **10. Validate** | Inputs actual lab measurement | Computes prediction error & health | Actual measured value (`4.95 S/cm`) | Error report (3.32%) & Health Log | Export PDF Report |

---

## OUTPUT 7: TROUBLESHOOTING GUIDE

| Error Symptom | Possible Cause | Troubleshooting Procedure |
|---|---|---|
| **Dashboard shows `Request failed with status code 422`** | Route path collision or backend server unprocessable request | Ensure Uvicorn server is running. Check `main.py` router order where `project_config.router` is mounted before `projects.router`. |
| **`ConnectionRefusedError: [WinError 10061]`** | FastAPI backend server on port 8000 is not running | Start backend: `$env:PYTHONPATH="backend"; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Upload warning: `An identical file already exists`** | SHA-256 hash match detected | File is already saved intact in storage. Duplicate upload prevented to preserve storage integrity. |
| **XRD Analysis Error: Missing required columns** | Raw CSV lacks 2-column format ($2\theta$, Intensity) | Open CSV file in text editor and ensure it contains 2 numeric columns separated by commas without extra headers. |
| **Optimization Warning: Model is RETIRED** | Selected ML model failed health check | Select an `APPROVED` model version on the Machine Learning page before generating candidates. |

---

## OUTPUT 8: GLOSSARY OF TERMINOLOGY

- **Applicability Domain**: Training feature boundary specifying the range of valid inputs where an ML model can make reliable predictions.
- **Central Composite Design (CCD)**: Design of Experiments (DOE) response surface methodology combining factorial, axial, and center points.
- **Crystallite Size ($D$)**: Average size of coherent crystalline domains derived via Scherrer equation ($D = \frac{K\lambda}{\beta\cos\theta}$).
- **FWHM**: Full Width at Half Maximum of a diffraction peak in radians.
- **Model Drift**: Degradation of machine learning prediction performance over time as new validation experiments are recorded.
- **Ohm's Law Fitting**: Linear regression fit of Voltage vs Current ($I = V/R$) to compute film resistance, resistivity, and conductivity.
- **ReportLab**: High-performance Python PDF document generation framework used for scientific report compilation.
- **Scherrer Equation**: Mathematical relation linking XRD peak broadening to crystallite domain size.
- **SHA-256**: Secure Hash Algorithm producing a 256-bit cryptographic fingerprint to guarantee file immutability.
- **Tauc Plot**: Optical absorption transformation $(\alpha h\nu)^{1/\gamma}$ vs $h\nu$ used to measure semiconductor band gaps.
