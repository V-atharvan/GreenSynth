# Changelog — GreenSynth Analytics

All notable changes to the GreenSynth Analytics Platform are documented in this file.

## [1.0.0-research] — 2026-08-10

### Added
- **Phase 20 — Production Hardening & Research Release Preparation**:
  - Enhanced `/health` and `/ready` application readiness endpoints.
  - Implemented `DataIntegrityService` for SHA-256 raw file checksum verification and database orphan detection.
  - Implemented CLI maintenance tools: `scripts/backup.py` and `scripts/restore.py` with manifest SHA-256 hash checks.
  - Added Data Integrity Audit APIs under `/api/v1/integrity/`.
  - Completed comprehensive documentation suite (`USER_GUIDE.md`, `RESEARCH_WORKFLOW.md`, `ADMIN_GUIDE.md`, `DEPLOYMENT.md`, `QUICK_START.md`, `TROUBLESHOOTING.md`, `RESEARCH_RELEASE_CHECKLIST.md`).
- **Phase 19 — Multi-Project Research Platform**:
  - Full configuration-driven support for all 8 laboratory projects (P1 to P8).
  - Shared synthesis method engines (`SolGelMethod`, `HydrothermalMethod`, `SprayPyrolysisMethod`).
  - Domain catalogs (Materials, Biomass, Extracts, Solvents, Methods).
  - `PropertyComparabilityService` enforcing cross-project scientific rules.
  - Interactive Project Synthesis Matrix dashboard in frontend.
- **Phase 18 — Evidence-Based Experimental Optimization & Candidate Generation**:
  - Objective scoring engine (`MAXIMIZE`, `MINIMIZE`, `TARGET`) with transparent score contribution breakdowns.
  - Search space bounds validation & hard/soft constraint evaluation.
  - Candidate generation (Grid Search, Random Search with seed, Model-guided Search).
  - Converter from candidate to PLANNED experiment for physical lab validation.
- **Phase 1–17 Core Systems**:
  - Complete XRD, UV-Vis, FTIR, SEM, Electrical characterization preprocessing & calculation modules.
  - Descriptive statistics, correlation matrices, OLS regression, ANOVA.
  - Full ML training, 5-Fold Cross Validation, model registry, versioning, applicability domain checks.
  - Closed-loop prediction error tracking and model health snapshots.
