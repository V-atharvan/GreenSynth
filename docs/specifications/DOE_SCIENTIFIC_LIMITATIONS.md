# Scientific Limitations & Boundary Disclaimers

## 1. Scope Boundary
- **Exploration vs Optimization**: Design of Experiments (DOE) provides structured sampling across factor space. It is distinct from global optimization algorithms (e.g. Bayesian Optimization).
- **Researcher Control**: All DOE conditions are generated as **`PROPOSED`** and require explicit researcher approval before becoming **`PLANNED`** laboratory experiments.
- **Data Integrity**: Failed laboratory experiments remain traceable in history and are never deleted. Missing response values are stored as `missing` without zero-filling or synthetic imputation.
- **Phase Boundary**: STOP after completing Phase 14 — DO NOT implement Phase 15 (Bayesian Optimization) automatically.
