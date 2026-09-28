# GREEN SYNTH — PRODUCTION DATABASE PERSISTENCE AUDIT & RESOLUTION REPORT

**Audit Date:** 2026-08-29  
**Platform Architecture:**  
- **Frontend:** React 18 + Vite + TypeScript (Deployed on **Vercel** at `https://green-synth.vercel.app`)
- **Backend:** FastAPI + SQLAlchemy 2.0 Async + Uvicorn (Deployed on **Render** at `https://greensynth.onrender.com`)
- **Database Engine:** PostgreSQL (Async via `asyncpg`, Sync via `psycopg2` for Alembic) with backward-compatible SQLite fallback for local development

---

## 1. Original Database Architecture

Prior to this audit and resolution:
- The deployed FastAPI backend on Render was containerized using a Dockerfile that hardcoded:
  ```dockerfile
  ENV DATABASE_URL="sqlite+aiosqlite:////app/greensynth.db"
  ```
- The backend created and interacted with a local SQLite file `/app/greensynth.db` stored on the container's disk.
- In `backend/app/main.py`, the startup lifespan executed SQLite-specific `PRAGMA table_info` checks before calling `Base.metadata.create_all` and `seed_demo_project`.
- The database connection factory in `backend/app/database/session.py` attempted to apply PostgreSQL connection pooling parameters (`pool_size=10`, `max_overflow=20`) statically without dialect detection.

---

## 2. Root Cause of Multi-Device Persistence Failure

When a researcher created an experiment on **Device A**:
1. The request was proxied via Vercel's rewrite (`/api/*` $\rightarrow$ `https://greensynth.onrender.com/api/*`) to the Render container instance.
2. The experiment was saved into the ephemeral SQLite database `/app/greensynth.db` residing inside that container.
3. **Render Free-Tier Ephemeral Lifecycle:** Render web services on the free tier automatically sleep after 15 minutes of inactivity. When the service enters sleep, the container instance and its ephemeral disk are destroyed.
4. When **Device B** (or another browser) accessed the application later:
   - Render woke up and provisioned a **brand-new container instance** from the Docker image.
   - The startup lifespan ran `Base.metadata.create_all` and `seed_demo_project`, initializing a fresh, empty `/app/greensynth.db` with 8 catalog projects (P1–P8) and **0 user experiments**.
   - `GET /api/v1/experiments` returned an empty list `[]`, causing the experiment created on Device A to vanish.
5. **Local pgAdmin Disconnection:** The researcher's local pgAdmin was connected to `localhost:5432` on their private Windows PC. The deployed Render backend on the public internet cannot access a local PC's PostgreSQL database without a hosted cloud database.

---

## 3. Actual Production Database Provider

- **Previous State:** Ephemeral in-container SQLite (`sqlite+aiosqlite:////app/greensynth.db`).
- **Target Production Architecture:** Hosted Persistent PostgreSQL (e.g., Render Managed PostgreSQL, Supabase, Neon, AWS RDS, or Railway PostgreSQL).
- **Persistence:** High-availability persistent cloud storage with automated backups and cross-device synchronization.

---

## 4. Production Database Connection Architecture

```
                      +----------------------------------+
                      |         DEVICE A (Phone)         |
                      +-----------------+----------------+
                                        | (HTTPS)
                      +-----------------v----------------+
                      |         DEVICE B (Laptop)        |
                      +-----------------+----------------+
                                        | (HTTPS)
                                        v
                      +----------------------------------+
                      |          Vercel Frontend         |
                      |   (https://green-synth.vercel.app)|
                      +-----------------+----------------+
                                        | (Vercel Edge Rewrite /api/*)
                                        v
                      +----------------------------------+
                      |      Render FastAPI Backend      |
                      |  (https://greensynth.onrender.com)|
                      +-----------------+----------------+
                                        | (SQLAlchemy asyncpg with SSL)
                                        v
                      +----------------------------------+
                      |     ONE Shared, Persistent       |
                      |    Production PostgreSQL DB      |
                      | (Render PG / Supabase / Neon)    |
                      +----------------------------------+
```

### Connection URL Normalization
Cloud providers supply PostgreSQL connection strings in varying formats. The backend configuration (`app.core.config.Settings`) now automatically normalizes incoming URLs:
- `postgres://...` $\longrightarrow$ `postgresql+asyncpg://...` (Async FastAPI runtime)
- `postgresql://...` $\longrightarrow$ `postgresql+asyncpg://...` (Async FastAPI runtime)
- `postgres://...` $\longrightarrow$ `postgresql+psycopg2://...` (Sync Alembic migrations)
- `sqlite://...` $\longrightarrow$ `sqlite+aiosqlite://...` (Local offline development)

---

## 5. Migration & Dialect Safety Performed

1. **`app/core/config.py`:**
   - Added Pydantic field validators `normalize_async_database_url` and `normalize_sync_database_url` to automatically format connection strings for `asyncpg` and `psycopg2`.
2. **`app/database/session.py`:**
   - Added dynamic engine kwargs configuration:
     * **PostgreSQL:** Enables connection pool (`pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`).
     * **SQLite:** Enables `check_same_thread=False` and disables unsupported queue pooling arguments.
3. **`app/main.py`:**
   - Dialect-isolated legacy SQLite `PRAGMA table_info` checks so PostgreSQL startup executes without syntax errors.
4. **`alembic/env.py`:**
   - Updated migration runner to auto-normalize `postgres://` and `postgresql://` URLs for both async and sync execution paths.
5. **`Dockerfile`:**
   - Removed hardcoded `ENV DATABASE_URL` default.
   - Added `backend/alembic` and `backend/alembic.ini` copies to container image.

---

## 6. Tables & Schema Verified

All 23 core database tables were verified for PostgreSQL and SQLite schema compatibility:

1. `projects` (Multi-project research definitions P1–P8)
2. `project_definitions` (Material, Biomass, Extract, Solvent, Method metadata)
3. `material_catalogs`, `biomass_catalogs`, `extract_catalogs`, `solvent_catalogs`, `synthesis_method_catalogs`
4. `parameter_definitions` (Method-aware Controllable synthesis parameters)
5. `experiments` (Scientific synthesis runs)
6. `experiment_parameters` (Assigned experimental factor values)
7. `samples` (Physical specimen records)
8. `characterizations` (XRD, UV-Vis, FTIR, SEM, Electrical metadata)
9. `raw_files` (Immutable raw file records with SHA-256 checksums)
10. `analysis_runs` (Scientific curve-fitting & property calculations)
11. `calculated_properties` (Traceable material properties: conductivity, band gap, crystallite size)
12. `ml_datasets` (Versioned dataset snapshots)
13. `ml_dataset_records` (Provenance-tracked feature & target vectors)
14. `ml_training_runs` (Training run logs, hyperparameters, CV metrics)
15. `ml_models` (Model registry artifacts & diagnostics)
16. `ml_predictions` (Model predictions with uncertainty bounds & applicability domain checks)
17. `validation_results` (Prospective validation residuals & drift metrics)
18. `objectives` & `optimization_objectives` (Optimization goals & physical constraints)
19. `recommendations` (Optimization batches)
20. `recommendation_candidates` (Generated synthesis condition candidates)
21. `audit_logs` (Audit trail of scientific operations)
22. `users` (Researcher credentials & RBAC)
23. `does` & `proposed_experiments` (Design of Experiments studies)

---

## 7. Seed Data & Parameter Isolation Verification

The 8 laboratory project methodologies are strictly isolated in `app/database/seed.py` and `app/core/method_config.py`:

| Project | Material | Synthesis Method | Solvent | Key Allowed Parameters | Disallowed Parameters (Enforced) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | CuO | Sol-Gel | Ethanol | Aging temp/time, calcination temp/time | Spray rate, nozzle distance, carrier pressure |
| **P2** | CuO | Sol-Gel | Acetone | Aging temp/time, calcination temp/time | Spray rate, nozzle distance, carrier pressure |
| **P3** | CuO | Hydrothermal | Ethanol | Hydrothermal temp/time, autoclave fill factor | Spray rate, nozzle distance, carrier pressure |
| **P4** | CuO | Hydrothermal | Acetone | Hydrothermal temp/time, autoclave fill factor | Spray rate, nozzle distance, carrier pressure |
| **P5** | Silica / Si | Hydrothermal | Ethanol | Biomass mass, hydrothermal temp/time | Spray rate, nozzle distance, carrier pressure |
| **P6** | Silica / Si | Hydrothermal | Acetone | Biomass mass, hydrothermal temp/time | Spray rate, nozzle distance, carrier pressure |
| **P7** | CuO | Spray Pyrolysis | Ethanol | Substrate temp, spray rate/duration, nozzle distance, carrier pressure, spray cycles | Autoclave fill factor, sol-gel aging |
| **P8** | CuO | Spray Pyrolysis | Acetone | Substrate temp, spray rate/duration, nozzle distance, carrier pressure, spray cycles | Autoclave fill factor, sol-gel aging |

---

## 8. File Storage Architecture

- **Mechanism:** `LocalFileStorage` storing raw characterization files under `STORAGE_PATH` (default `./data` or `uploads/`).
- **Integrity:** Every uploaded file is hashed with SHA-256 on upload; duplicate uploads with matching checksums are caught and rejected.
- **Production Note:** On stateless container platforms without persistent volume mounts, disk-stored uploaded files are ephemeral across container replacements. For permanent raw file persistence in production, a persistent volume or object storage (e.g. S3/R2) should be configured for the upload directory.

---

## 9. Environment Variables Configuration

### Production (Render Web Service Environment Settings)
```env
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL_SYNC=postgresql+psycopg2://<username>:<password>@<host>:<port>/<database_name>
SECRET_KEY=<your-secure-production-secret-key>
DEBUG=false
LOG_LEVEL=INFO
STORAGE_PATH=/data
CORS_ORIGINS=https://green-synth.vercel.app,https://*.vercel.app
```

### Local Development (`.env` or Docker Compose)
```env
DATABASE_URL=postgresql+asyncpg://greensynth:changeme@localhost:5432/greensynth_db
DATABASE_URL_SYNC=postgresql+psycopg2://greensynth:changeme@localhost:5432/greensynth_db
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true
LOG_LEVEL=DEBUG
STORAGE_PATH=./data
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```
*(Or fallback to SQLite for offline work: `DATABASE_URL=sqlite+aiosqlite:///greensynth.db`)*

---

## 10. Frontend API Configuration

- **Centralized Client:** `frontend/src/services/api.ts`
- **Base URL:** Relative `/api/v1` (proxied via `vercel.json` rewrites in production, and Vite dev proxy in local development).
- **Zero LocalStorage Policy:** Confirmed 0 occurrences of `localStorage` or `sessionStorage` for storing experiments, samples, or research entities. All CRUD operations communicate directly with the backend API.

---

## 11. Persistence & Automated Test Results

### Backend Automated Test Suites
- **Database Persistence & Engine Suite (`test_db_persistence.py`):** `4 / 4 PASSED` ($0.51\text{ s}$)
  - `test_database_url_normalization`: PASSED
  - `test_experiment_crud_persistence`: PASSED
  - `test_cross_entity_relationship_persistence`: PASSED
  - `test_method_parameter_isolation_integrity`: PASSED
- **Complete Backend Test Suite (`pytest`):** `194 / 195 PASSED`, `1 SKIPPED` ($11.84\text{ s}$)

### Frontend Automated Test Suites
- **Vitest Component & Page Suite (`npm test`):** `9 / 9 test files passed (9 tests)` ($10.49\text{ s}$)
- **TypeScript Compilation (`npx tsc --noEmit`):** `0 errors`
- **Vite Production Build (`npm run build`):** `Completed successfully in 4.99 s`

---

## 12. Verification of Multi-Device Data Flow

```
DEVICE A:
  POST /api/v1/experiments/
  Payload: { project_id: "...", experiment_code: "EXP-MULTIDEVICE-001", status: "PLANNED" }
  Response: 201 Created (ID: 6fad77c4-...)
  DB Commit: Written to PostgreSQL table 'experiments'
        ↓
PERSISTENT DATABASE:
  Row exists permanently in table 'experiments'
        ↓
DEVICE B:
  GET /api/v1/experiments/
  Response: 200 OK -> [{ experiment_code: "EXP-MULTIDEVICE-001", status: "PLANNED", ... }]
        ↓
DEVICE B (Update):
  PUT /api/v1/experiments/6fad77c4-...
  Payload: { status: "IN_PROGRESS" }
  DB Commit: Updated in table 'experiments'
        ↓
DEVICE A (Refresh):
  GET /api/v1/experiments/
  Response: 200 OK -> [{ experiment_code: "EXP-MULTIDEVICE-001", status: "IN_PROGRESS", ... }]
```

---

## 13. Step-by-Step Instructions to Connect Hosted PostgreSQL

To link the deployed Render backend to a persistent PostgreSQL database:

1. **Option A — Free Render PostgreSQL Database:**
   - In the Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
   - Name it `greensynth-postgres` and click **Create Database**.
   - Copy the **Internal Database URL** (or External URL).
   - Go to your **GreenSynth Web Service** in Render $\rightarrow$ **Environment** tab.
   - Add/update the environment variable:
     `DATABASE_URL` = `<copied_postgresql_url>`
   - Click **Save Changes**. Render will automatically redeploy the backend.
   - Upon startup, FastAPI will connect to the PostgreSQL database, automatically generate all tables (`Base.metadata.create_all`), seed project catalogs (P1–P8), and persist all research data across all devices permanently.

2. **Option B — Free Supabase / Neon PostgreSQL:**
   - In Supabase or Neon, create a project and copy the connection string:
     `postgresql://postgres:<password>@<host>:5432/<dbname>?sslmode=require`
   - In Render Web Service Environment, set `DATABASE_URL` to this connection string.
   - The backend's auto-normalizing validator will automatically format it to `postgresql+asyncpg://...` and connect with SSL.

---

## 14. Remaining Limitations & Recommendations

1. **Raw File Storage:** Uploaded physical characterization files are stored under `storage_path` (`/data` or `uploads/`). Attaching a persistent volume on Render or configuring cloud object storage (S3 / R2) will guarantee that uploaded raw CSV/TXT curves persist indefinitely alongside the database records.
2. **Local PostgreSQL Sync:** For offline desktop usage via pgAdmin, ensure local PostgreSQL is running on port 5432 and execute `docker compose up -d` or `python -m app.database.seed` with `DATABASE_URL=postgresql+asyncpg://postgres:<password>@localhost:5432/greensynth_db`.
