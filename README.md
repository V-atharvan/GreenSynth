# GreenSynth Analytics Platform

**Data-Driven Experimental Analysis and Optimization System for Green Synthesis of Semiconductor Materials**

Version 0.1.0 — Phase 1 (Project Foundation)

---

## Overview

GreenSynth Analytics is a full-stack research software platform designed to connect laboratory experimental data with scientific characterisation analysis (XRD, UV-Vis, FTIR, SEM, Electrical), statistical comparison, and evidence-based experimental optimization.

### Core Scientific Principles
1. **Traceability:** Every calculated result is traceable to raw file + method + formula + algorithm version.
2. **Category Isolation:** Data categories (`MEASURED`, `CALCULATED`, `STATISTICAL`, `PREDICTED`, `VALIDATED`) are strictly isolated and labeled.
3. **Immutability:** Raw experimental data files are never overwritten once finalized.
4. **Configuration-Driven:** Projects (P1 through P8) are defined via configuration metadata, not hard-coded in business logic.
5. **Scientifically Honest:** No fake scientific results, no unvalidated ML predictions, no claiming an experiment is universally "best".

---

## Technology Stack

- **Frontend:** React 18, TypeScript, Vite, CSS Modules / Custom CSS Design System
- **Backend:** Python 3.11, FastAPI, Pydantic v2
- **Database:** PostgreSQL 16, SQLAlchemy 2.0 (Async), Alembic migrations
- **Testing:** Pytest (backend), Vitest (frontend)
- **Code Quality:** Ruff, Black, Mypy, ESLint
- **Containerization:** Docker, Docker Compose

---

## Repository Structure

```
CRTD/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/             # REST Route handlers (/projects, /experiments, /samples, /dashboard, /health)
│   │   ├── core/            # Config (pydantic-settings) & logging
│   │   ├── database/        # Async SQLAlchemy session, Base, and seed data
│   │   ├── models/          # ORM models (User, Project, Experiment, Sample)
│   │   ├── schemas/         # Pydantic v2 schemas (validation & response models)
│   │   ├── services/        # Service layer (business logic orchestration)
│   │   ├── scientific/      # [Stub] Pure scientific calculation modules (Phase 6+)
│   │   ├── analytics/       # [Stub] Comparative and statistical analytics (Phase 10+)
│   │   ├── ml/              # [Stub] Machine learning pipelines & gating (Phase 14+)
│   │   ├── optimization/    # [Stub] DOE & optimization engines (Phase 13+)
│   │   ├── ingestion/       # [Stub] Raw data parsing & ingestion (Phase 5+)
│   │   └── storage/         # FileStorageBackend abstraction (Phase 5+)
│   ├── alembic/             # Database migration scripts
│   ├── tests/               # Pytest test suite (unit & integration)
│   └── pyproject.toml
│
├── frontend/                 # React + TypeScript + Vite Application
│   ├── src/
│   │   ├── components/      # UI components (StatusBadge, PageHeader, LoadingSpinner, ConfirmModal, etc.)
│   │   ├── pages/           # Pages (Dashboard, Projects, ProjectDetail, Experiments, ExperimentDetail, Samples, SampleDetail)
│   │   ├── layouts/         # MainLayout with collapsible sidebar
│   │   ├── services/        # API service layer (axios client + projectService, experimentService, etc.)
│   │   ├── types/           # TypeScript interfaces mirroring backend schemas
│   │   └── index.css        # Global CSS design system
│   └── package.json
│
├── data/                     # Persistent Data Storage
│   ├── raw/                 # Original laboratory data files (immutable)
│   ├── processed/           # Processed datasets
│   └── exports/             # Exported reports
│
├── docs/                     # Architecture & Spec Documentation
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Environment variables template
└── README.md
```

---

## Quick Start (Docker Compose)

The easiest way to start the entire development stack is with Docker Compose:

```bash
# 1. Clone & enter directory
git clone <repository-url>
cd CRTD

# 2. Copy environment file
cp .env.example .env

# 3. Start services with Docker Compose
docker compose up --build
```

### Services & Ports:
- **Frontend UI:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **FastAPI Interactive Docs:** `http://localhost:8000/docs`
- **PostgreSQL Database:** `localhost:5432`

---

## Local Development (Without Docker)

### Backend Setup:
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests

### Backend Tests (Pytest):
```bash
cd backend
pytest
```

### Frontend Tests (Vitest):
```bash
cd frontend
npm run test
```

---

## Phase 1 Status & Seed Data

Phase 1 provides the complete application foundation:
- Database schema: `users`, `projects`, `experiments`, `samples` tables.
- Seed Data: **Project 7 DEMO metadata** (`P7` — Phytochemical synthesis of CuO via spray pyrolysis using mulberry extract in ethanol) is automatically seeded into PostgreSQL on startup if not present.
- **Zero Fabricated Results:** Seed data contains ONLY configuration metadata — no fake measurements, characterisations, or ML predictions exist.

---

## License

Research Platform — Proprietary / Academic License
