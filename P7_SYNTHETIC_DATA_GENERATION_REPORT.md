# GreenSynth Analytics — Project P7 Synthetic Research Dataset Generation & End-to-End Workflow Report

> [!CAUTION]
> **SCIENTIFIC INTEGRITY DISCLAIMER**  
> **THIS IS STRICTLY SYNTHETIC / SIMULATED RESEARCH DATA GENERATED SPECIFICALLY FOR PLATFORM STRESS-TESTING, DATABASE INTEGRITY VERIFICATION, AND MACHINE LEARNING PIPELINE BENCHMARKING.**  
> **IT MUST NEVER BE CITED, PUBLISHED, OR MISREPRESENTED AS REAL EMPIRICAL LABORATORY MEASUREMENTS.**

---

## 1. Executive Summary

This report documents the creation, physics-based simulation, database ingestion, and end-to-end workflow verification of a large-scale, reproducible synthetic research dataset for:

**Project P7:** *Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis*

- **Target Material:** Nanocrystalline Copper Oxide ($\text{CuO}$) Thin Films
- **Reducing & Capping Agent:** Mulberry (*Morus*) Leaf Phytochemical Extract
- **Solvent:** Ethanol ($\text{C}_2\text{H}_5\text{OH}$)
- **Deposition Technique:** Ultrasonic Pneumatic Spray Pyrolysis
- **Primary ML Target Property:** Electrical Conductivity ($\sigma$, unit: $\text{S/cm}$)
- **Deterministic Random Seed:** `20260928`
- **Lead Provenance Identity:** `GreenSynth Synthetic Research Team`
- **Execution Date:** September 28, 2026

```
SYNTHESIS CONDITIONS (13 Parameters)
  ├── Substrate Temp (174 - 477 °C)
  ├── Precursor Conc (0.08 - 0.45 M)
  ├── Mulberry Extract (0.2 - 40.3 g/L, 5 - 55 mL)
  └── Spray Dynamics (Rate, Dur, Dist, Press, Cycles)
         │
         ▼
DEPOSITION & THIN FILM FORMATION
  ├── Thermal pyrolysis & nucleation kinetics
  ├── Phytochemical capping & grain growth inhibition
  └── Film continuity & thickness (70 - 950 nm)
         │
         ▼
INSTRUMENTAL CHARACTERIZATION (1,380 Runs)
  ├── XRD: Monoclinic CuO peaks (32.5°, 35.5°, 38.7°, 48.7°) -> Crystallite Size (10.5 - 32.6 nm)
  ├── UV-Vis: Fundamental direct absorption edge -> Optical Band Gap (1.35 - 1.72 eV)
  ├── FTIR: Cu-O vibrational modes (535, 595 cm⁻¹) & Phytochemical bands (1055, 1635, 2925, 3370 cm⁻¹)
  └── Electrical: Linear Ohmic I-V sweeps -> Resistance (Ω), Resistivity (Ω·cm), Conductivity (S/cm)
         │
         ▼
SCIENTIFIC DERIVATIONS & DATABASE INGESTION
  ├── Ingested into live Neon PostgreSQL database (400 experiments, 412 samples, 1,380 raw files)
  ├── 1,881 calculated property instances traceable to analytical runs
  └── Zero database corruption; 7 pre-existing demo experiments fully preserved
         │
         ▼
ML PIPELINE BENCHMARKING
  ├── Feature Extraction (13 controllable synthesis factors, zero target leakage)
  ├── 5-Fold Cross-Validation across 5 Model Architectures
  ├── Model Comparison (Baseline, Linear, Ridge, Random Forest, Gradient Boosting)
  └── Prediction Inference with 95% Confidence Intervals & Applicability Domain Check
```

---

## 2. Experimental Design Matrix (Groups A–H)

The dataset encompasses **400 experiments** (`P7-SYNTH-001` through `P7-SYNTH-400`) structured across 8 controlled Design of Experiments (DOE) groups:

| Group Code | Run Range | Run Count | Focus & Scientific Rationale | Key Varied Factors |
| :--- | :--- | :--- | :--- | :--- |
| **Group A** | `001`–`050` | 50 | **Baseline Screening**: Broad screening across full operational ranges to map general response contours. | $T_\text{sub}$ ($220$–$440^\circ\text{C}$), $C_\text{prec}$ ($0.08$–$0.45\text{ M}$), Substrates |
| **Group B** | `051`–`120` | 70 | **Substrate Temperature Factorial**: Systematic temperature sweep to identify crystallization threshold and phase purity. | $T_\text{sub}$ ($180$–$480^\circ\text{C}$) $\times$ $C_\text{prec}$ ($0.10, 0.20, 0.35\text{ M}$) |
| **Group C** | `121`–`190` | 70 | **Phytochemical Optimization**: Examining capping efficiency, grain boundary passivation, and carbon impurity limits. | Extract conc ($1$–$40\text{ g/L}$) $\times$ Extract vol ($5$–$55\text{ mL}$) |
| **Group D** | `191`–`250` | 60 | **Spray Dynamics & Deposition Kinetics**: Evaluating liquid delivery rate, droplet evaporation, and cycle pauses. | Spray rate ($1.2$–$9\text{ mL/min}$), gas pressure, cycles |
| **Group E** | `251`–`290` | 40 | **Nozzle Geometry & Stagnation Layer**: Investigating nozzle-to-substrate distance and thermal boundary effects. | Distance ($10$–$35\text{ cm}$) $\times$ Gas pressure $\times$ Spray rate |
| **Group F** | `291`–`340` | 50 | **Substrate & Environmental Sensitivity**: Comparative substrate performance under ambient humidity/temperature swings. | Glass, FTO Glass, ITO Glass, Quartz, Silicon |
| **Group G** | `341`–`380` | 40 | **Response Surface (RSM / CCD)**: 4-factor orthogonal central composite matrix for non-linear interaction modeling. | $T_\text{sub}$, $C_\text{prec}$, $C_\text{ext}$, $V_\text{ext}$ |
| **Group H** | `381`–`400` | 20 | **Replication & Variance Testing**: Exact replicates of central operating conditions producing dual physical specimens (S01, S02). | Central optimum: $365^\circ\text{C}$, $0.20\text{ M}$, $16\text{ g/L}$, $20\text{ mL}$ |

---

## 3. Physical & Chemical Governing Formulations

All simulated instrumental spectra, curves, and calculated properties were derived from established physical and chemical kinetics of spray pyrolyzed metal oxides:

### A. Film Thickness ($t_\text{nm}$)
$$t_\text{nm} = 260.0 \times \left(\frac{C_\text{prec}}{0.20}\right) \times \left(\frac{V_\text{delivered}}{100.0}\right) \times \eta_\text{thermal} \times \left(\frac{20.0}{d_\text{nozzle}}\right)^{1.6} \times \left(0.85 + 0.15 \frac{P_\text{gas}}{200.0}\right)$$
- $\eta_\text{thermal} = \frac{1}{1 + \exp(-0.025(T_\text{sub} - 230.0))}$ represents thermal droplet evaporation and precursor pyrolytic decomposition efficiency.
- Log-normal random variation ($\sigma = 0.04$) accounts for spray plume turbulence.

### B. Monoclinic CuO Crystallite Size ($D$, nm)
$$D = D_\text{thermal} \times \text{Capping} \times \text{PrecursorFactor} + \epsilon_D$$
- $D_\text{thermal} = 10.0 + \frac{26.0}{1 + \exp(-0.018(T_\text{sub} - 330.0))}$ models thermally activated grain growth.
- $\text{Capping} = 1.0 - 0.22 \min\left(\frac{C_\text{ext}}{30.0}, 1.0\right) - 0.08 \min\left(\frac{V_\text{ext}}{40.0}, 1.0\right)$ represents polyphenol/flavonoid capping inhibiting crystallite agglomeration.
- Scherrer equation applied to instrumental XRD patterns: $D = \frac{K \lambda}{\beta \cos\theta}$ with Cu $\text{K}\alpha$ radiation ($\lambda = 0.15406\text{ nm}$, $K = 0.9$).

### C. Direct Optical Band Gap ($E_g$, eV)
$$E_g = 1.35 + \frac{55.0}{(D + 3.0)^2} + 0.035 \left(\frac{C_\text{ext}}{30.0}\right) - 0.0003(T_\text{sub} - 350.0) + \epsilon_{Eg}$$
- Quantum confinement size shift ($\propto 1/D^2$) elevates $E_g$ from the bulk CuO limit ($1.35\text{ eV}$) up to $1.72\text{ eV}$ in ultrafine crystallites.
- Tauc relation applied to UV-Vis spectra: $(\alpha h\nu)^2 \propto (h\nu - E_g)$.

### D. Electrical Transport & Conductivity ($\sigma$, S/cm)
$$\sigma = \sigma_\text{peak} \times \left[0.02 + 0.98 f_T \times (0.35 + 0.65 f_C) \times (0.30 + 0.70 f_E) \times f_\text{film}\right] \times f_\text{sub} \times f_\text{hum} \times \exp(\epsilon_\sigma)$$
- $f_T = \exp\left(-\frac{(T_\text{sub} - 370.0)^2}{2(65.0)^2}\right)$ models optimal copper-vacancy p-type carrier density peaking at $370^\circ\text{C}$ (below $220^\circ\text{C}$ incomplete pyrolysis suppresses conduction; above $450^\circ\text{C}$ grain boundary defects increase).
- $f_E = x \exp(1 - x)$ where $x = C_\text{ext}/16.0$ captures the dual role of phytochemicals (optimal passivation at $15$–$20\text{ g/L}$, but insulating carbonaceous phase segregation at $>35\text{ g/L}$).
- Film continuity factor $f_\text{film} = \frac{1}{1 + \exp(-0.03(t_\text{nm} - 140.0))}$ accounts for percolation limits in ultra-thin films.
- Resistivity $\rho = 1/\sigma$ and Resistance $R = \rho \frac{L}{W \times t}$ verified via linear regression slope of I-V sweeps.

---

## 4. Controlled Imperfections & Missingness Profile

To realistically evaluate GreenSynth's data cleaning, filtering, and ML exclusion mechanisms, controlled scientific imperfections were injected:

- **Experiment Status Breakdown:**
  - `COMPLETED`: 382 experiments ($95.5\%$)
  - `FAILED`: 12 experiments ($3.0\%$) — film peeling, substrate thermal shock, or extreme thickness non-uniformity (e.g. at $T_\text{sub} > 470^\circ\text{C}$ with high spray rates).
  - `IN_PROGRESS`: 4 experiments ($1.0\%$)
  - `PLANNED`: 2 experiments ($0.5\%$)
- **Characterization Technique Missingness:**
  - $68\%$ of completed runs have complete 4-technique characterization suites (XRD, UV-Vis, FTIR, Electrical).
  - $20\%$ are missing 1 technique (e.g. UV-Vis or FTIR omitted due to instrument queue).
  - $9\%$ have only 2 techniques (XRD + Electrical).
  - $3\%$ have single-technique characterization.
- **Replicate Pairs (Group H):**
  - Runs `P7-SYNTH-381` to `P7-SYNTH-400` produced independent duplicate specimens (`S01` and `S02`) tested independently under identical nominal synthesis parameters to benchmark intra-batch variance ($CV \approx 3.8\%$).

---

## 5. Live Database Ingestion & Verification Audit

The dataset was ingested directly into the Neon PostgreSQL instance via `scripts/ingest_p7_synthetic_data.py`. All records were committed in 16 atomic batches with zero table locking or data corruption.

### Post-Ingestion Record Audit

| Database Entity | Pre-Existing Count | Added Synthetic Records | Post-Ingestion Verified Count | Growth Factor |
| :--- | :--- | :--- | :--- | :--- |
| **`experiments`** (Project P7) | 7 | 400 | **407** | $58.1\times$ |
| **`experiment_parameters`** | 105 | 6,000 | **6,105** | $58.1\times$ |
| **`samples`** | 4 | 412 | **416** | $104.0\times$ |
| **`characterizations`** | 10 | 1,380 | **1,390** | $139.0\times$ |
| **`raw_files`** (Stored & Hash Verified) | 10 | 1,380 | **1,390** | $139.0\times$ |
| **`analysis_runs`** | 10 | 1,380 | **1,390** | $139.0\times$ |
| **`calculated_properties`** | 9 | 1,881 | **1,890** | $210.0\times$ |
| **`CalculatedProperty` (Conductivity)** | 1 | 394 | **395** | $395.0\times$ |

### Data Integrity & Provenance Verification
1. **Foreign Key Integrity:** $100\%$ of `experiment_parameters`, `samples`, `characterizations`, `raw_files`, and `calculated_properties` link validly to active P7 entities.
2. **Immutability & Checksums:** Every raw file in `data/raw/` matches its SHA-256 database digest with `storage_backend = 'local'`.
3. **Existing Data Preservation:** Pre-existing demo records (`P7-EXP-001` through `P7-EXP-007`) and projects P1–P6, P8 remain completely unaltered.

---

## 6. Machine Learning Pipeline Benchmark

The ML pipeline was executed directly via `scripts/run_p7_ml_pipeline.py` using `MLDatasetService`, `MLTrainingService`, and `MLPredictionService`.

### A. Dataset Build & Quality Validation
- **Dataset Name:** `P7 CuO Spray Pyrolysis Conductivity Dataset` (ID: `49d0ab52-4876-47cb-9230-228930792bc1`)
- **Target Property:** `Electrical Conductivity` (Unit: `S/cm`, Type: `CALCULATED`)
- **Features (13 Controllable Synthesis Parameters):**
  1. `substrate_temperature_c` (°C)
  2. `precursor_concentration` (mol/L)
  3. `precursor_solution_volume` (mL)
  4. `mulberry_extract_concentration` (g/L)
  5. `mulberry_extract_volume` (mL)
  6. `ethanol_volume` (mL)
  7. `spray_rate_ml_min` (mL/min)
  8. `spray_duration_min` (min)
  9. `nozzle_substrate_distance_cm` (cm)
  10. `carrier_gas_pressure_kpa` (kPa)
  11. `spray_cycles` (cycles)
  12. `ambient_temperature_c` (°C)
  13. `ambient_relative_humidity` (%)
- **Target Leakage Prevention:** Upstream characterization properties (XRD crystallite size, optical band gap) were strictly excluded from the feature space.
- **Dataset Eligibility Audit:**
  - Total candidate observations evaluated: 416
  - **Eligible observations:** **395** ($95.0\%$)
  - **Excluded observations:** **21** ($5.0\%$)
    - `INCOMPLETE_EXPERIMENT`: 18 observations (12 `FAILED` + 4 `IN_PROGRESS` + 2 `PLANNED`)
    - `MISSING_TARGET`: 3 observations (runs without electrical I-V characterization)

### B. 5-Fold Cross-Validation Performance Comparison

Five candidate regression algorithms were trained, evaluated across 5-fold cross-validation, and serialized into the Model Registry:

| Model Architecture | Model Status | Train $R^2$ | CV $R^2$ (Test) | CV RMSE (S/cm) | CV MAE (S/cm) | Overfitting Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MEAN_BASELINE** | `TRAINED` | $0.0000$ | $-0.0050$ | $0.2625$ | $0.2112$ | None (Dummy predictor) |
| **LINEAR_REGRESSION** | `VALIDATED` | $0.3930$ | $0.3019$ | $0.2166$ | $0.1724$ | Low |
| **RIDGE** | `VALIDATED` | $0.3930$ | $0.3023$ | $0.2166$ | $0.1724$ | Low ($\alpha = 1.0$) |
| **GRADIENT_BOOSTING** | `VALIDATED` | $0.8921$ | $0.6360$ | $0.1558$ | $0.1243$ | Moderate |
| **RANDOM_FOREST** ⭐ | `VALIDATED` | **$0.9578$** | **$0.6685$** | **$0.1501$** | **$0.1214$** | **Selected Champion** |

> [!NOTE]
> **Scientific Model Interpretation:**  
> The linear models capture only ~30% of the variance because the true physics of spray pyrolysis exhibits strong non-linear thresholds: an optimal substrate crystallization peak ($370^\circ\text{C}$), an extract capping/passivation optimum ($16\text{ g/L}$), and geometric nozzle spreading. Non-linear ensemble methods (`Random Forest` and `Gradient Boosting`) successfully model these non-linearities, cutting prediction error by **43%** ($\text{RMSE}$ drops from $0.2625$ to $0.1501\text{ S/cm}$).

### C. Champion Model Prediction & Applicability Verification
A test inference query was executed on the champion model using central composite operating factors:
- **Input Conditions:**
  - $T_\text{sub} = 370.0^\circ\text{C}$, $C_\text{prec} = 0.22\text{ M}$, $V_\text{prec} = 80.0\text{ mL}$
  - $C_\text{ext} = 16.0\text{ g/L}$, $V_\text{ext} = 20.0\text{ mL}$, $V_\text{eth} = 150.0\text{ mL}$
  - $\text{Spray Rate} = 4.2\text{ mL/min}$, $\text{Duration} = 25.0\text{ min}$, $\text{Distance} = 20.0\text{ cm}$
  - $P_\text{gas} = 210.0\text{ kPa}$, $\text{Cycles} = 20$
  - Ambient: $24.5^\circ\text{C}$, $45.0\%$ RH
- **Inference Output:**
  - **Predicted Electrical Conductivity:** **$0.6449\text{ S/cm}$**
  - **95% Confidence Interval:** $[0.3507, 0.9391]\text{ S/cm}$ (via residual variance estimation)
  - **Applicability Domain Check:** `VALID` (all 13 factors confirmed within training domain bounds)
  - **Audit Logged:** Prediction instance persisted in `ml_predictions` table.

---

## 7. Downstream Workflow Integration (DOE & Studio Readiness)

To demonstrate closed-loop research capability, `scripts/test_p7_downstream_doe.py` generated a Central Composite Design (CCD) study directly from the active project configuration:

- **DOE Study Name:** `P7 Central Composite Design — Conductivity Optimization`
- **Method:** `CENTRAL_COMPOSITE` (Response Surface Methodology)
- **Target Response:** Maximize `Electrical Conductivity`
- **Controllable Factors Evaluated:**
  1. $T_\text{sub}$: $300.0$ to $420.0^\circ\text{C}$ (center $360.0^\circ\text{C}$)
  2. $C_\text{prec}$: $0.10$ to $0.35\text{ M}$ (center $0.22\text{ M}$)
  3. $C_\text{ext}$: $5.0$ to $30.0\text{ g/L}$ (center $17.5\text{ g/L}$)
  4. $V_\text{ext}$: $10.0$ to $40.0\text{ mL}$ (center $25.0\text{ mL}$)
- **Design Matrix Generated:** **29 proposed experiments** (`RUN-001` through `RUN-029`) combining factorial vertices, axial star points, and 4 replicated center-points.
- **Traceability:** Fully registered under `does` and `proposed_experiments` tables, ready for one-click conversion into planned laboratory runs.

---

## 8. Artifact & Data File Manifest

All generated synthetic research files are systematically cataloged and stored within the repository:

```
synthetic_data/p7/
├── README.md                                  # Dataset documentation and scientific integrity disclaimer
├── dataset_manifest.json                      # Full structured manifest of 400 runs, samples, & characterizations
├── dataset_statistics.json                    # Statistical summary of distributions and property metrics
├── experiments_summary.csv                    # Flat CSV table of all 400 experiments and parameter values
├── calculated_properties_summary.csv          # Flat CSV table of 1,881 calculated property instances
├── validation_report.json                     # Database ingestion count and foreign-key integrity audit
├── ml_pipeline_results.json                   # Complete ML benchmark metrics, CV scores, & prediction outputs
├── doe_test_results.json                      # Downstream Central Composite Design matrix output
└── raw/
    ├── xrd/                                   # 390 synthetic XRD patterns (two_theta, intensity)
    ├── uvvis/                                 # 309 synthetic UV-Vis spectra (wavelength_nm, absorbance)
    ├── ftir/                                  # 287 synthetic FTIR spectra (wavenumber_cm1, transmittance_pct)
    └── electrical/                            # 394 synthetic I-V sweeps (voltage_v, current_a)

data/raw/projects/P7/                          # Live repository raw storage hierarchy
└── experiments/
    └── P7-SYNTH-001 ... P7-SYNTH-400/
        └── samples/
            └── .../
                └── {characterization_id}/
                    └── *.csv                  # SHA-256 verified raw instrumental files
```

---

## 9. Conclusion & Validation Summary

1. **Scale & Performance:** GreenSynth successfully ingested **400 experiments, 412 samples, 1,380 characterization files, and 1,881 calculated property records** into a live Neon PostgreSQL database without schema modifications or table locks.
2. **Scientific Realism:** Physics-derived responses faithfully mirror literature for spray pyrolyzed CuO semiconductors, demonstrating realistic crystallization thresholds, phytochemical capping kinetics, optical absorption edges, and Ohmic transport.
3. **Data Quality & Handling:** Controlled imperfections (12 failed runs, missing techniques, 20 duplicate replicate pairs) validated the platform's missing-data filters and ML eligibility rules.
4. **End-to-End Pipeline Cohesion:**
   $$\text{DOE} \longrightarrow \text{Experiments} \longrightarrow \text{Samples} \longrightarrow \text{Raw Characterization} \longrightarrow \text{Calculations} \longrightarrow \text{ML Dataset} \longrightarrow \text{Model Training} \longrightarrow \text{Prediction} \longrightarrow \text{Optimization}$$
   The entire workflow was executed and verified without breaking architectural boundaries.
5. **Production Readiness:** The platform is fully operational, verified, and equipped to support both computational modeling and real physical laboratory campaigns for Project P7.

