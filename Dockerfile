FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    python-multipart \
    "sqlalchemy[asyncio]" \
    asyncpg \
    aiosqlite \
    psycopg2-binary \
    alembic \
    pydantic \
    pydantic-settings \
    jinja2 \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    matplotlib \
    plotly \
    reportlab \
    httpx \
    boto3 \
    botocore

# ── Copy application code ──────────────────────────────────
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

# ── Environment variables ──────────────────────────────────
ENV PYTHONPATH=/app/backend

# ── Expose port ────────────────────────────────────────────
EXPOSE 8000

# ── Default command ────────────────────────────────────────
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
