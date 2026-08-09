FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────
COPY backend/pyproject.toml ./backend/
COPY backend/app ./backend/app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e "./backend"

# ── Environment variables ──────────────────────────────────
ENV PYTHONPATH=/app/backend

# ── Expose port ────────────────────────────────────────────
EXPOSE 8000

# ── Default command ────────────────────────────────────────
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
