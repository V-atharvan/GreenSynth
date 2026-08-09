# GreenSynth Analytics — Platform Administration & Maintenance Guide

## System Administration & Maintenance Commands

### 1. Creating System Backups
To create a complete timestamped backup ZIP archive containing the SQLite database, raw file storage, and cryptographic SHA-256 manifest:

```powershell
& "C:\Users\Atharva\AppData\Local\Programs\Python\Launcher\py.exe" scripts/backup.py
```

Output:
`backups/greensynth_backup_YYYYMMDD_HHMMSS.zip`

### 2. Restoring System Backups
To restore the platform from a backup archive with SHA-256 verification:

```powershell
& "C:\Users\Atharva\AppData\Local\Programs\Python\Launcher\py.exe" scripts/restore.py backups/greensynth_backup_YYYYMMDD_HHMMSS.zip
```

### 3. Data Integrity & Storage Verification API
- `POST /api/v1/integrity/verify-storage` — Scans raw file directory and verifies SHA-256 hashes against database records.
- `POST /api/v1/integrity/verify-database` — Scans for relational orphan records.
- `GET /api/v1/integrity/report` — Generates complete system audit report.

### 4. Health & Readiness Endpoints
- `GET /health` — Returns application version and system status.
- `GET /ready` — Returns 200 OK when database and file storage are fully operational.
