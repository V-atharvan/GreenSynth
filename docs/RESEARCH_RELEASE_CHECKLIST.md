# GreenSynth Analytics — Research Release Checklist (v1.0.0-research)

## Release Readiness Verification

- [x] **Data Integrity**: Cryptographic SHA-256 checksums calculated on all raw file uploads.
- [x] **Raw File Immutability**: Raw laboratory files are immutable once saved.
- [x] **Data Classification**: UI explicitly labels `RAW`, `PROCESSED`, `CALCULATED`, `STATISTICAL`, `PREDICTED`, `RECOMMENDED`, `VALIDATED`.
- [x] **Multi-Project Support**: All 8 laboratory projects (P1 to P8) configured with shared synthesis method engines.
- [x] **Scientific Calculations**: XRD Scherrer crystallite size, UV-Vis Tauc band gap, Electrical conductivity Ohm fitting verified.
- [x] **ML & Validation**: K-Fold Cross Validation, Applicability Domain bounds, Closed-loop prediction error tracking.
- [x] **Optimization Engine**: Multi-objective scoring, search space bounds validation, candidate generation & PLANNED experiment converter.
- [x] **System Maintenance**: `scripts/backup.py` and `scripts/restore.py` tested and operational.
- [x] **Health & Readiness**: `/health` and `/ready` endpoints active.
- [x] **Automated Tests**: 100% backend pytest unit tests passing.
- [x] **Frontend Build**: Vite production bundle compiled with 0 TypeScript/Vite errors.
- [x] **Documentation Suite**: User Guide, Workflow, Admin Guide, Deployment, Troubleshooting, Quick Start, Scientific Methods complete.
