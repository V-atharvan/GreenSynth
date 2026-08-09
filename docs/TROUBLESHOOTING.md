# GreenSynth Analytics — Troubleshooting & Resolution Guide

## Common Issues & Solutions

### 1. Database Connection Failure
- **Symptom**: `/health` returns `"database": "unreachable"`.
- **Solution**: Ensure `greensynth.db` exists in project root, or run `python -m app.database.seed` to re-initialize SQLite database tables.

### 2. Missing File or Checksum Mismatch
- **Symptom**: Integrity report flags `"missing_files"` or `"checksum_mismatches"`.
- **Solution**: Run `POST /api/v1/integrity/verify-storage` or execute `scripts/restore.py` to restore intact raw files from backup archive.

### 3. Invalid XRD File Upload
- **Symptom**: Error *"Unable to process XRD file because required 2θ and intensity data columns are missing."*
- **Solution**: Ensure your raw XRD `.csv` file contains two numeric columns ($2\theta$ angle and counts/intensity). Header lines are automatically skipped.

### 4. Retired Model Blocked in Optimization
- **Symptom**: Error *"Optimization blocked: Selected model is RETIRED."*
- **Solution**: In **Machine Learning** (`/ml`), select an `APPROVED` or `VALIDATED` model version for candidate generation.

### 5. Out-of-Domain Prediction Warning
- **Symptom**: Candidate condition flagged `OUT_OF_DOMAIN`.
- **Solution**: Input parameter values exceed the model's training range. Check `allow_out_of_domain` box if exploratory investigation is intended.
