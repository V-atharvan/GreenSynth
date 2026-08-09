# GreenSynth Analytics — Researcher User Guide

## Introduction
GreenSynth Analytics is a data-driven experimental analysis, statistical modeling, machine learning, and evidence-based optimization platform for green synthesis of semiconductor materials (specifically mulberry-extract mediated synthesis of CuO thin films/nanoparticles via Spray Pyrolysis, Sol-Gel, and Hydrothermal methods).

---

## Data Classification Badges
To maintain complete scientific clarity, all information displayed in the UI is labeled:
- `[RAW DATA]` — Original uncalibrated laboratory measurement files (XRD, UV-Vis, FTIR, SEM, Electrical).
- `[PROCESSED DATA]` — Software preprocessed data (baseline corrected, normalized).
- `[CALCULATED DATA]` — Derived physical values (Band Gap $E_g$, Crystallite Size $D$, Electrical Conductivity $\sigma$).
- `[STATISTICAL DATA]` — Statistical summaries, correlation matrices, ANOVA, regression.
- `[PREDICTED DATA]` — Machine learning property estimates with 95% confidence bounds.
- `[RECOMMENDED DATA]` — Promising candidate experimental conditions.
- `[VALIDATED DATA]` — Experimentally verified prediction results.

---

## Core Operations

### 1. Navigating Research Projects (P1–P8)
Navigate to **Projects** (`/projects`) to view the **Multi-Project Synthesis Matrix**:
- **P1**: CuO + Mulberry + Ethanol + Sol-Gel
- **P2**: CuO + Mulberry + Acetone + Sol-Gel
- **P3**: CuO + Mulberry + Ethanol + Hydrothermal
- **P4**: CuO + Mulberry + Acetone + Hydrothermal
- **P5**: Silica/Silicon + Rice Husk + Mulberry + Ethanol + Hydrothermal
- **P6**: Silica/Silicon + Rice Husk + Mulberry + Acetone + Hydrothermal
- **P7**: CuO + Mulberry + Ethanol + Spray Pyrolysis (*MVP*)
- **P8**: CuO + Mulberry + Acetone + Spray Pyrolysis

### 2. Creating Experiments & Entering Synthesis Parameters
1. Go to **Experiments** (`/experiments`) and click **+ New Experiment**.
2. Select your research project (e.g. Project 7).
3. Fill in required parameters:
   - Copper precursor salt & concentration (mol/L)
   - Mulberry extract concentration (g/L) & volume (mL)
   - Solvent volume (mL)
   - Substrate temperature (°C) & Spray rate (mL/min)
4. Save experiment to generate experiment code (`EXP-P7-xxx`).

### 3. Registering Samples & Uploading Raw Files
1. Create a physical **Sample** record (`SAMP-P7-xxx`) linked to your experiment.
2. In Sample Detail, upload raw characterization files (XRD `.csv`/`.xy`, UV-Vis `.csv`, FTIR `.csv`, SEM `.png`, Electrical `.csv`).
3. Cryptographic SHA-256 checksums are calculated immediately on upload.

### 4. Running Scientific Characterization Analysis
- **XRD Analysis**: Peak detection, FWHM calculation, Scherrer crystallite size derivation ($D = \frac{K\lambda}{\beta \cos\theta}$).
- **UV-Vis Analysis**: Tauc plot linear extrapolation for optical bandgap ($(\alpha h\nu)^{1/\gamma}$ vs $h\nu$).
- **Electrical Analysis**: I-V slope fitting for resistivity $\rho$ and electrical conductivity $\sigma$.

### 5. Training ML Models & Candidate Optimization
1. Build ML dataset in **Machine Learning** (`/ml`).
2. Train regression models (Ridge, Random Forest, Gradient Boosting) with 5-Fold Cross Validation.
3. In **Evidence-Based Optimization** (`/optimization`), configure objectives (`MAXIMIZE`, `MINIMIZE`, `TARGET`) and generate ranked candidate experimental conditions.
4. Convert promising candidates to **PLANNED** experiments for physical laboratory validation.
