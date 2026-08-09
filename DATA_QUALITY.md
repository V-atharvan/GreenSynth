# Data Quality Dashboard & Outlier Traceability

## 1. Data Quality Checks
Evaluates missing scientific measurements, potential duplicate records, unit consistency, and replicate consistency (`PASS`, `WARNING`, `ERROR`).

## 2. Outlier Traceability (No Automatic Deletion)
- Configurable IQR ($1.5 \times \text{IQR}$) and Z-score ($|Z| > 3.0$) outlier detection **FLAGS** potential outliers.
- Original measurements are never overwritten or deleted.
- Store method, threshold, observation value, researcher decision, and decision date.
