# GreenSynth Analytics — Project P7 Data Schema & Workflow Audit
**Document ID:** `P7-DATA-SCHEMA-AUDIT-20260928`  
**Target Project:** `P7` (*Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis*)  
**Material System:** CuO Thin Films  
**Plant Extract:** Mulberry (*Morus*) Extract  
**Solvent:** Ethanol  
**Synthesis Method:** Spray Pyrolysis  
**Audit Date:** September 28, 2026  
**Auditor:** Antigravity Research Assistant  

---

## 1. Executive Summary

This schema and architectural audit verifies the exact GreenSynth Analytics repository structure, database entities, foreign-key relationships, parameter definitions, scientific calculation services, ML pipeline interfaces, and file storage mechanisms prior to generating the 400-experiment synthetic dataset.

Every layer of the GreenSynth workflow has been inspected directly in the active source code and live database (Neon Serverless PostgreSQL).

```
PROJECT (P7: 268fa4a4-a396-4749-9621-39f1a9129684)
  │
  ├── PARAMETER DEFINITIONS (15 spray pyrolysis parameters in `parameter_definitions`)
  │
  └── EXPERIMENT (`experiments` table)
        │
        ├── EXPERIMENT PARAMETERS (`experiment_parameters` table — immutable values)
        │
        └── SAMPLE (`samples` table, 1-2 per experiment)
              │
              └── CHARACTERIZATION (`characterizations` table — XRD, UV_VIS, FTIR, SEM, ELECTRICAL)
                    │
                    ├── RAW FILE (`raw_files` table, storage under `data/raw/`)
                    │
                    └── ANALYSIS RUN (`analysis_runs` table)
                          │
                          ├── PROCESSED FILE (`processed_files` table, under `data/processed/`)
                          ├── XRD PEAKS (`xrd_peaks` table, 2θ, intensity, FWHM)
                          ├── SEM METADATA / ANNOTATIONS (`sem_metadata`, `sem_annotations`)
                          └── CALCULATED PROPERTY (`calculated_properties` table)
                                ├── Crystallite Size (nm) via Scherrer Equation
                                ├── Optical Band Gap (eV) via Tauc Extrapolation
                                ├── Electrical Resistance (Ohm) via Ohm's Law Regression
                                ├── Electrical Resistivity (Ohm*cm) via Geometric Formula
                                └── Electrical Conductivity (S/cm) via Reciprocal Resistivity [PRIMARY ML TARGET]
                                      │
                                      ▼
                                ML DATASET BUILDER (`ml_datasets` & `ml_dataset_records`)
                                      │
                                      ▼
                                MODEL REGISTRY & TRAINING (`ml_models` & `ml_training_runs`)
                                      │
                                      ▼
                                PREDICTION & APPLICABILITY DOMAIN (`ml_predictions`)
                                      │
                                      ▼
                                DESIGN OF EXPERIMENTS (`objectives`, `does`, `proposed_experiments`)
                                      │
                                      ▼
                                RECOMMENDATION & CLOSED LOOP (`recommendations`, `recommendation_candidates`)
```

---

## 2. Target Project Identification

- **Project ID in Database:** `268fa4a4-a396-4749-9621-39f1a9129684`
- **Project Code:** `P7`
- **Official Name:** `Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis`
- **Material:** `CuO`
- **Extract:** `Mulberry`
- **Solvent:** `Ethanol`
- **Synthesis Method:** `Spray Pyrolysis`
- **Status:** `ACTIVE`

---

## 3. Actual Experiment Schema (`experiments`)

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, default `uuid4` | Unique experiment identifier |
| `project_id` | `UUID` | Foreign Key (`projects.id`, RESTRICT) | Must equal `268fa4a4-a396-4749-9621-39f1a9129684` |
| `experiment_code` | `String(64)` | Unique, Indexed, NOT NULL | Deterministic code, e.g. `P7-SYNTH-001` to `P7-SYNTH-400` |
| `title` | `String(512)` | NOT NULL | Descriptive title, e.g. `P7 Synthetic Spray Pyrolysis Run 001` |
| `status` | `String(16)` | NOT NULL, Indexed | Enum: `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `ARCHIVED` |
| `experiment_date` | `Date` | Nullable | Date experiment was conducted |
| `researcher` | `String(255)` | Nullable | Preserves provenance: `"GreenSynth Synthetic Research Team"` |
| `notes` | `Text` | Nullable | Prominent synthetic notice and group assignment metadata |
| `created_at` | `DateTime(tz)` | Server default `now()` | UTC creation timestamp |
| `updated_at` | `DateTime(tz)` | Server default `now()` | UTC update timestamp |

---

## 4. Actual Parameter Definitions Schema (`parameter_definitions` & `experiment_parameters`)

### A. The 15 P7 Parameter Definitions (Registered in `parameter_definitions` for P7)

| Parameter Code | Display Name | Data Type | Unit | Min | Max | Allowed Values |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `copper_precursor_salt` | Copper Precursor Salt | `TEXT` | `None` | `None` | `None` | Constant: `"Copper acetate monohydrate"` |
| `precursor_concentration` | Precursor Concentration | `NUMBER` | `mol/L` | `0.001` | `2.0` | Target operational: `0.05`–`0.50` |
| `precursor_solution_volume` | Precursor Solution Volume | `NUMBER` | `mL` | `1.0` | `500.0` | Target operational: `20.0`–`200.0` |
| `mulberry_extract_concentration` | Mulberry Extract Concentration | `NUMBER` | `g/L` | `0.1` | `100.0` | Target operational: `1.0`–`40.0` |
| `mulberry_extract_volume` | Mulberry Extract Volume | `NUMBER` | `mL` | `0.1` | `100.0` | Target operational: `5.0`–`60.0` |
| `ethanol_volume` | Ethanol Volume | `NUMBER` | `mL` | `1.0` | `500.0` | Target operational: `50.0`–`300.0` |
| `substrate_type` | Substrate Type | `ENUM` | `None` | `None` | `None` | `['Glass', 'FTO Glass', 'ITO Glass', 'Quartz', 'Silicon']` |
| `substrate_temperature_c` | Substrate Temperature | `NUMBER` | `°C` | `100.0` | `600.0` | Target operational: `200.0`–`450.0` |
| `spray_rate_ml_min` | Spray Rate | `NUMBER` | `mL/min` | `0.1` | `20.0` | Target operational: `1.0`–`10.0` |
| `spray_duration_min` | Spray Duration | `NUMBER` | `min` | `0.5` | `120.0` | Target operational: `5.0`–`60.0` |
| `nozzle_substrate_distance_cm` | Nozzle-to-Substrate Distance | `NUMBER` | `cm` | `5.0` | `50.0` | Target operational: `10.0`–`35.0` |
| `carrier_gas_pressure_kpa` | Carrier Gas Pressure | `NUMBER` | `kPa` | `10.0` | `500.0` | Target operational: `100.0`–`350.0` |
| `spray_cycles` | Number of Spray Cycles | `NUMBER` | `cycles` | `1.0` | `100.0` | Target operational: `5.0`–`50.0` |
| `ambient_temperature_c` | Ambient Temperature | `NUMBER` | `°C` | `15.0` | `40.0` | Target operational: `20.0`–`32.0` |
| `ambient_relative_humidity` | Ambient Relative Humidity | `NUMBER` | `%` | `10.0` | `95.0` | Target operational: `30.0`–`75.0` |

### B. Recorded Parameter Values (`experiment_parameters`)

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Parameter instance identifier |
| `experiment_id` | `UUID` | Foreign Key (`experiments.id`, CASCADE) | Parent experiment |
| `parameter_definition_id` | `UUID` | Foreign Key (`parameter_definitions.id`, RESTRICT) | Template definition |
| `value` | `Text` | Nullable | String value (e.g. `"Glass"` or `"0.25"`) |
| `value_numeric` | `Float` | Nullable, Indexed | Parsed float for queries & ML extraction |
| `unit` | `String(64)` | Nullable | Unit preserved at time of experiment |
| `notes` | `Text` | Nullable | Parameter notes |

---

## 5. Actual Sample Schema (`samples`)

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key | Unique sample identifier |
| `experiment_id` | `UUID` | Foreign Key (`experiments.id`, RESTRICT) | Must link to existing experiment |
| `sample_code` | `String(64)` | Unique, Indexed, NOT NULL | Deterministic code: `P7-SYNTH-001-S01`, `P7-SYNTH-001-S02` |
| `name` | `String(255)` | NOT NULL | e.g. `CuO Thin Film on Glass - Run 001` |
| `material` | `String(128)` | Nullable | Fixed to `"CuO"` |
| `description` | `Text` | Nullable | Film description & substrate context |
| `status` | `String(16)` | NOT NULL, Indexed | Enum: `PREPARED`, `READY_FOR_CHARACTERIZATION`, `UNDER_ANALYSIS`, `COMPLETED`, `ARCHIVED` |
| `notes` | `Text` | Nullable | Replicate indicator, provenance notice |

---

## 6. Actual Characterization & File Schema (`characterizations`, `raw_files`)

### A. Characterization Run (`characterizations`)
- `technique`: `String(32)` — strictly one of `XRD`, `UV_VIS`, `FTIR`, `SEM`, `ELECTRICAL`.
- `status`: `UPLOADED`, `READY_FOR_ANALYSIS`, `PROCESSING`, `ANALYZED`, `ARCHIVED`.
- `operator`: `"Synthetic Instrument Simulator"`.
- `instrument_name`, `instrument_model`: Specific to characterization technique.

### B. Raw Files (`raw_files`)
- `original_filename`: Standardized naming (e.g. `xrd_pattern.csv`, `uvvis_spectrum.csv`, `ftir_spectrum.csv`, `iv_curve.csv`, `sem_micrograph.png`).
- `stored_path`: Follows repository storage hierarchy: `projects/{project_code}/experiments/{exp_code}/samples/{sample_code}/{ch_id}/{filename}` under `data/raw/`.
- `checksum`: SHA-256 hash computed over file bytes (enforces duplicate detection).
- `storage_backend`: `"local"` (with optional S3).
- `file_metadata`: Stores synthetic provenance dictionary: `{"data_origin": "SYNTHETIC", "random_seed": 20260928}`.

---

## 7. Actual Scientific Calculation Engine (`analysis_runs`, `calculated_properties`)

GreenSynth computes derived properties via native analytical engines:

1. **Electrical I-V Analysis Engine** ([backend/app/scientific/electrical/](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/Project/CRTD/backend/app/scientific/electrical/)):
   - **Parser:** Reads `voltage_v` and `current_a` (or mV, mA, uA).
   - **Calculation 1:** Linear regression slope gives **Electrical Resistance** ($R$, unit: $\Omega$, method: `Ohm's Law Linear Regression`).
   - **Calculation 2:** Using film dimensions (length $L$, width $W$, thickness $t$), cross-sectional area $A = W \times t$, calculates **Electrical Resistivity** ($\rho = R \times A / L$, unit: $\Omega\cdot\text{cm}$, method: `Geometric Resistance Formula`).
   - **Calculation 3 (Primary Target):** $\sigma = 1 / \rho$ gives **Electrical Conductivity** (unit: $\text{S/cm}$, method: `Reciprocal Resistivity`).
   - **CalculatedProperty name in DB:** `"Electrical Conductivity"`, unit: `"S/cm"`.

2. **XRD Analysis Engine** ([backend/app/scientific/xrd/](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/Project/CRTD/backend/app/scientific/xrd/)):
   - **Parser:** Reads `two_theta` and `intensity`.
   - **Peak Detection:** Scipy `find_peaks` identifies peak position ($2\theta$), intensity, prominence, and FWHM ($\beta$).
   - **Calculation:** Scherrer equation $D = \frac{K \lambda}{\beta \cos\theta}$ gives **Crystallite Size** (unit: $\text{nm}$, method: `Scherrer Equation`).
   - **CalculatedProperty name in DB:** `"Crystallite Size"`, unit: `"nm"`.

3. **UV-Vis Analysis Engine** ([backend/app/scientific/uvvis/](file:///c:/Users/Atharva/OneDrive/Documents/Atharva/Project/CRTD/backend/app/scientific/uvvis/)):
   - **Parser:** Reads `wavelength_nm` and `absorbance`.
   - **Tauc Transform:** $(\alpha h\nu)^{1/n}$ vs $h\nu$ ($n=1/2$ for direct band gap CuO).
   - **Calculation:** Linear extrapolation of absorption edge gives **Optical Band Gap** (unit: $\text{eV}$, method: `Tauc Plot Linear Extrapolation`).
   - **CalculatedProperty name in DB:** `"Optical Band Gap"`, unit: `"eV"`.

---

## 8. Actual ML Dataset Builder Schema (`ml_datasets`, `ml_dataset_records`)

The `MLDatasetService` automatically binds the synthesis parameters to calculated properties:
- **Project Filter:** `MLDataset.project_id == P7`
- **Target Extraction:** Queries `CalculatedProperty` where `property_name == "Electrical Conductivity"` and `unit == "S/cm"`.
- **Feature Extraction:** Queries `ExperimentParameter` joined to `ParameterDefinition`, mapping parameter codes directly into a JSON feature dictionary:
  1. `precursor_concentration` (mol/L)
  2. `precursor_solution_volume` (mL)
  3. `mulberry_extract_concentration` (g/L)
  4. `mulberry_extract_volume` (mL)
  5. `ethanol_volume` (mL)
  6. `substrate_temperature_c` (°C)
  7. `spray_rate_ml_min` (mL/min)
  8. `spray_duration_min` (min)
  9. `nozzle_substrate_distance_cm` (cm)
  10. `carrier_gas_pressure_kpa` (kPa)
  11. `spray_cycles` (cycles)
  12. `ambient_temperature_c` (°C)
  13. `ambient_relative_humidity` (%)
- **Leakage Prevention:** Characterization features (such as XRD peak width, crystallite size, or band gap) must NOT be selected as input features when predicting electrical conductivity.
- **Provenance Field:** `MLDataset.is_synthetic = True` is natively supported.

---

## 9. Actual ML Training & Prediction

- **Algorithms:** `RANDOM_FOREST`, `GRADIENT_BOOSTING`, `RIDGE`, `LASSO`, `LINEAR_REGRESSION`, `MEAN_BASELINE`.
- **Grouping:** Supported by `MLDatasetRecord.experiment_id` to prevent replicate leakage across train/test folds.
- **Evaluation:** 5-fold cross-validation with $R^2$, RMSE, MAE.
- **Applicability Domain:** Min/max feature bounding box check in `ApplicabilityChecker`.
- **Uncertainty:** Residual variance-based confidence intervals in `UncertaintyEstimator`.

---

## 10. Actual Downstream Modules (DOE, Optimization, Recommendation, Validation)

- **DOE (`does`, `proposed_experiments`):** Supports Full Factorial, Fractional Factorial, CCD, Box-Behnken designs for P7 factors.
- **Optimization (`optimization_runs`, `optimization_candidates`):** Multi-objective evaluation (e.g., maximize conductivity, target band gap).
- **Recommendation Studio (`recommendations`):** Generates candidate synthesis conditions with human-in-the-loop review.
- **Validation Studio (`validation_criteria`, `holdout_validations`):** Compares predictions against measured values.

---

## 11. Schema Constraints & Limitations Identified

1. **Synthetic Data Provenance:**
   - Database has `is_synthetic` on `ml_datasets`.
   - For `experiments`, `samples`, and `raw_files`, provenance must be stored in `researcher`, `notes`, and `file_metadata`.
2. **Replicate Grouping:**
   - Multi-sample experiments share `experiment_id`. The ML pipeline groups by `experiment_id` to prevent data leakage.
3. **No Overwrite / Truncation:**
   - The active database contains 7 demo experiments and 8 project templates. Ingestion must be strictly additive and isolated using `P7-SYNTH-xxx` codes.
4. **Transaction Safety:**
   - Database insertions must occur within atomic transactions with automatic rollback on error.

---

**Audit Conclusion:** The GreenSynth Analytics architecture fully supports the end-to-end P7 synthetic research workflow without any schema changes.
