# GreenSynth Analytics — 5-Minute Researcher Quick Start

## Quick Start Steps

### 1. Launching Application
- **Backend API**: Running on `http://127.0.0.1:8000` (Docs: `/docs`)
- **Frontend Dashboard**: Running on `http://localhost:5173`

### 2. Selecting Research Project
Open **Projects** (`/projects`) and select your target research project:
- **Project 7**: CuO + Mulberry + Ethanol + Spray Pyrolysis (MVP)
- **Project 8**: CuO + Mulberry + Acetone + Spray Pyrolysis
- **Project 1–6**: Sol-Gel & Hydrothermal synthesis options

### 3. Entering Experiment & Characterization Data
1. Navigate to **Experiments** → **+ New Experiment**.
2. Input synthesis parameters (Precursor, Concentration, Extract volume, Substrate Temperature).
3. Create a **Sample** record under the experiment.
4. Upload raw XRD, UV-Vis, or Electrical measurement `.csv` files.
5. Click **Analyze Characterization** to compute:
   - XRD crystallite size ($D$)
   - UV-Vis optical bandgap ($E_g$)
   - Electrical conductivity ($\sigma$)

### 4. Running Optimization & Machine Learning
1. Navigate to **Machine Learning** (`/ml`) to view trained models.
2. Go to **Experimental Optimization** (`/optimization`).
3. Set your target objective (e.g. `MAXIMIZE conductivity_s_cm`).
4. Generate ranked candidate experimental conditions.
5. Click **🔬 Create Experiment** to convert a candidate into a PLANNED experiment for physical lab trial!
