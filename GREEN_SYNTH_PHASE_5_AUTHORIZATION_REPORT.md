# GREEN SYNTH ANALYTICS PLATFORM
## PHASE 5 — BACKEND AUTHORIZATION & PROJECT-LEVEL DATA ISOLATION REPORT

**Author**: Senior Backend Architect & Security Engineer  
**Status**: 100% Complete, Validated, and Verified  
**Date**: August 30, 2026  

---

### Executive Summary

Phase 5 introduces comprehensive backend authorization and strict, multi-tenant project-level data isolation for the **GreenSynth Analytics Platform**. In accordance with the Phase 5 specification:
1. **Server-Side Project Resolution**: The backend never trusts client-supplied `project_id` values. Project context is securely derived via `User` $\rightarrow$ `GroupMembership` $\rightarrow$ `ResearchGroup` $\rightarrow$ `Project`.
2. **Query-Level Database Scoping**: All resource queries (`experiments`, `samples`, `characterizations`, `raw_files`, `analysis_runs`, `ml_models`, `datasets`, `optimization_runs`, `evidence_records`, `dashboard_statistics`) execute with strict SQLAlchemy `WHERE` and `JOIN` filters scoped to the caller's authorized `current_project.id`.
3. **Zero Information Leakage & Anti-Enumeration Protection**: Foreign entity UUID lookups outside the user's project resolve to HTTP `404 Not Found` (or HTTP `403 Forbidden` on explicit project mismatch) with zero metadata leakage.
4. **Leader vs. Member Role Enforcement**: No global Admin role exists. Privileged actions such as member invitations and token regenerations require `is_leader=True`.
5. **Zero Scientific Distortion**: All mathematical algorithms, machine learning models, characterization peak finding, and thermodynamic formulations remain 100% unaltered.

---

### 1. Architectural Model & Lineage

```
                          ┌──────────────┐
                          │     User     │
                          └──────┬───────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │    GroupMembership    │ (status = ACTIVE)
                     └───────────┬───────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │    ResearchGroup    │ (status = ACTIVE)
                      └──────────┬──────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     Project     │ (current_project)
                        └────────┬────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│  Experiments │          │  ML Models   │            │ Optimization │
│  & Samples   │          │  & Datasets  │            │ & Validation │
└──────────────┘          └──────────────┘            └──────────────┘
```

---

### 2. Centralized Authorization Dependencies (`backend/app/api/deps.py`)

- `get_current_user`: Decodes JWT Bearer token, asserts user active status in database.
- `get_current_membership`: Resolves the active `GroupMembership` for the authenticated user (raises 403 `NO_ACTIVE_GROUP` if unassigned).
- `get_current_group`: Resolves the active `ResearchGroup` for the membership (raises 403 `NO_ACTIVE_GROUP` if group inactive or unassigned).
- `get_current_project`: Resolves the active `Project` bound to the group (raises 403 `NO_ACTIVE_PROJECT` if unassigned or inactive).
- `verify_project_access(project_id, current_project)`: Validates that any route or payload `project_id` matches `current_project.id` (raises 403 `PROJECT_ACCESS_DENIED` on mismatch).
- `get_current_leader`: Enforces `membership.is_leader is True` (raises 403 `LEADER_REQUIRED` for non-leaders).

---

### 3. Route & Service Hardening Summary (15 Router Modules + Services)

| Module | Scoping & Authorization Applied |
| :--- | :--- |
| **`routes/experiments.py`** | Injected `current_project`. Scoped `GET /` to `project_id`. `POST /` enforces `current_project.id`. `GET /{id}`, `PUT /{id}`, `DELETE /{id}` verify ownership; foreign IDs return 404. |
| **`routes/samples.py`** | Scoped `GET /` joining `Experiment.project_id == current_project.id`. `POST /` verifies parent experiment belongs to `current_project`. Foreign sample IDs return 404. |
| **`routes/characterizations.py`** | `POST /` checks parent sample project. `GET /{id}` and sample list endpoints scoped to `current_project`. |
| **`routes/files.py`** | `GET /{file_id}` and `GET /{file_id}/download` verify file $\rightarrow$ characterization $\rightarrow$ sample $\rightarrow$ experiment $\rightarrow$ project ownership. Foreign IDs return 404. |
| **`routes/parameters.py`** | `verify_project_access` on parameter definitions. Experiment parameter routes verify experiment ownership. |
| **`routes/reports.py`** | PDF and summary export routes verify experiment belongs to `current_project.id`. |
| **`routes/analytics.py`** | Dataset CRUD, sample comparison tables, statistical analysis runs, and CSV exports verify `verify_project_access`. |
| **`routes/doe.py`** | DOE preview, generation, listing, approval, regeneration, proposed experiment conversion, and CSV exports verify `verify_project_access`. |
| **`routes/recommendations.py`** | Generation, retrieval, candidate actions, modifications, and experiment creation verify `verify_project_access`. |
| **`routes/ml.py`** | Dataset creation/retrieval, training runs, model registry, predictions, drift monitoring, health checks, reviews, and retirement verify `verify_project_access`. |
| **`routes/optimization.py`** | Objectives, constraints, search space validation, optimization runs, candidate selection/rejection, and experiment conversion verify `verify_project_access`. |
| **`routes/validation.py`** | Criteria, holdout validation, prospective experiments, result linking, retraining triggers, candidate queue, and promotion verify `verify_project_access`. |
| **`routes/evidence.py`** | Scoped dataset versions, evidence records, approval workflows, and markdown reports to `current_project.id`. |
| **`routes/dashboard.py`** | Injected `current_project`; statistics (`total_experiments`, `total_samples`, `status_breakdown`, `recent_experiments`) scoped exclusively to `current_project.id`. |
| **`routes/analysis.py`** | FTIR, SEM, Electrical, UV-Vis, and XRD routes verify characterization, raw file, and analysis run project lineage before execution. |
| **`routes/projects.py`** | Scoped project listing and single project access to `current_project`. Leader creating new project binds group to that project. |
| **`services/sample_service.py`** | Added `project_id` join scoping to `get_all` and `get_by_id`. |
| **`services/characterization_service.py`** | Added `project_id` join scoping to `get_by_id`, `list_sample_characterizations`, `get_raw_file_by_id`, and `download_raw_file`. |
| **`services/dashboard_service.py`** | Added project-scoping to experiment count, sample count, status count, and recent experiments queries. |

---

### 4. Verification & Test Results

#### A. Cross-Project Isolation Test Suite (`tests/integration/test_project_isolation.py`)
- **16 of 16 isolation tests passed** (100% success rate):
  1. `test_unauthenticated_requests_rejected`: 401 Unauthorized across all protected routes.
  2. `test_user_without_active_group_rejected`: 403 NO_ACTIVE_GROUP.
  3. `test_user_a_cannot_read_project_b_experiment`: 404 Not Found (Zero leakage).
  4. `test_user_a_cannot_read_project_b_sample`: 404 Not Found.
  5. `test_user_a_cannot_read_project_b_characterization`: 404 Not Found.
  6. `test_user_a_cannot_download_project_b_raw_file`: 404 Not Found.
  7. `test_user_a_cannot_access_project_b_ml_assets`: 404 Not Found.
  8. `test_user_a_cannot_mutate_or_delete_project_b_experiment`: 404 Not Found.
  9. `test_user_a_cannot_create_sample_under_project_b_experiment`: 403/404.
  10. `test_user_a_cannot_pass_project_b_id_in_parameters`: 403/404.
  11. `test_collection_queries_are_strictly_scoped`: User A queries only return Project A data.
  12. `test_doe_execution_isolated`: 403 PROJECT_ACCESS_DENIED.
  13. `test_ml_prediction_isolated`: 404 Not Found.
  14. `test_report_generation_isolated`: 404 Not Found.
  15. `test_dashboard_statistics_scoped_to_project`: Scoped accurately.
  16. `test_member_cannot_perform_leader_operations`: 403 LEADER_REQUIRED.

#### B. Complete Backend Test Suite
- **254 Passed, 10 Skipped, 0 Failed** across 264 test items.
- Execution time: ~24.78 seconds.

#### C. Frontend Verification
- **11 Test Files Passed, 13 Tests Passed** (Vitest).
- **TypeScript**: `npx tsc --noEmit` exited with 0 errors.

---

### 5. Sign-Off

Phase 5 requirements have been met in full without breaking existing scientific logic or introducing security regressions.
GreenSynth Analytics Platform is ready for **Phase 6: Frontend Auth & Group State Integration**.
