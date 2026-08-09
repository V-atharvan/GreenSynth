# Machine Learning Model Registry & Artifact Management

## 1. Lifecycle Statuses
- `DRAFT`: Initial training configuration.
- `TRAINED`: Algorithm fitted and cross-validated.
- `VALIDATED`: Satisfies cross-validation quality threshold ($R^2 > 0$).
- `APPROVED`: Explicitly approved by researcher for future candidate optimization.
- `REJECTED`: Rejected during researcher review.
- `ARCHIVED`: Superseded by newer model versions.

## 2. Artifact Integrity & SHA256 Checksum
When saving a scikit-learn pipeline bundle (`model.joblib`), `ModelArtifactStore` computes a SHA256 hash stored in `artifact_hash`. Deserialization verifies the checksum to detect file tampering.
