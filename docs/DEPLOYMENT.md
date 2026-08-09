# GreenSynth Analytics — System Requirements & Deployment Guide

## System Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python Runtime**: Python 3.10+ (Recommended Python 3.12)
- **Node.js Runtime**: Node.js 18+ & npm 9+
- **Database**: SQLite (default local development) or PostgreSQL 14+
- **Disk Space**: Minimum 2 GB for application and raw characterization file storage

## Environment Variables (.env)
```env
APP_NAME="GreenSynth Analytics"
APP_VERSION="1.0.0-research"
ENVIRONMENT="production"
DEBUG=False
SECRET_KEY="your-production-secret-key-here"
DATABASE_URL="sqlite+aiosqlite:///./greensynth.db"
UPLOAD_DIR="uploads"
LOG_LEVEL="INFO"
```

## Production Deployment Steps

### 1. Backend Service (FastAPI / Uvicorn)
```powershell
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run database seed & initialization
python -m app.database.seed

# Launch production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Frontend Application (Vite / React)
```powershell
cd frontend
npm install
npm run build
```
Serve `frontend/dist/` using NGINX or Caddy.

### 3. Readiness Verification
Verify readiness endpoint returns 200 OK:
`GET http://localhost:8000/ready`
