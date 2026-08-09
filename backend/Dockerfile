FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ────────────────────────────
# Copy only dependency file first to leverage Docker layer cache
COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

# ── Copy application code ──────────────────────────────────
COPY . .

# ── Expose port ────────────────────────────────────────────
EXPOSE 8000

# ── Default command (overridden by docker-compose) ─────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
