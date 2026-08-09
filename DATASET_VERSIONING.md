# Dataset Versioning & Inclusion/Exclusion Rules

## 1. Immutability Principle
A dataset version (e.g. `PROJECT7-DOE01-DATASET (v1.0)`) is an immutable snapshot representing exact included sample IDs, included DOE runs, included factors, included responses, filtering rules, and exclusion rules.

## 2. Version Progression
Modifying filters or inclusion criteria generates version `v2.0`, preserving `v1.0` in historic records for auditability and reproducibility.

## 3. Explicit Exclusion Tracking
Excluded records explicitly record exclusion reasons: `MISSING_RESPONSE`, `INVALID_MEASUREMENT`, `FAILED_EXPERIMENT`, `OUT_OF_RANGE`, `DUPLICATE`, `DATA_QUALITY_ISSUE`, `RESEARCHER_EXCLUSION`, `INSTRUMENT_ERROR`. Raw measurements are never silently discarded or overwritten.
