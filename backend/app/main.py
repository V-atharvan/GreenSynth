"""
GreenSynth Analytics — FastAPI Application Entry Point

This module creates the FastAPI application, registers middleware,
exception handlers, and includes all API routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

# ── Configure logging before anything else ─────────────────
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.

    On startup:
      1. Create tables if needed
      2. Seed demo project data if database is empty
    """
    logger.info("=== GreenSynth Analytics starting up ===")
    logger.info("Version: %s | Debug: %s", settings.app_version, settings.debug)

    from app.database.base import Base
    from app.database.session import async_engine, AsyncSessionLocal
    from app.database.seed import seed_demo_project

    # Drop empty legacy 'does' & 'proposed_experiments' tables if missing columns so create_all builds clean schema
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import text
            res = await session.execute(text("PRAGMA table_info(does)"))
            cols = {row[1] for row in res.fetchall()}
            if cols and ("research_question" not in cols or "version" not in cols):
                cnt_res = await session.execute(text("SELECT COUNT(*) FROM does"))
                if cnt_res.scalar() == 0:
                    await session.execute(text("DROP TABLE does"))
                    await session.commit()
                    logger.info("Dropped empty legacy 'does' table for clean schema creation.")

            res_pe = await session.execute(text("PRAGMA table_info(proposed_experiments)"))
            cols_pe = {row[1] for row in res_pe.fetchall()}
            if cols_pe and "is_center_point" not in cols_pe:
                cnt_pe = await session.execute(text("SELECT COUNT(*) FROM proposed_experiments"))
                if cnt_pe.scalar() == 0:
                    await session.execute(text("DROP TABLE proposed_experiments"))
                    await session.commit()
                    logger.info("Dropped empty legacy 'proposed_experiments' table for clean schema creation.")
        except Exception as exc:
            logger.warning("Schema check warning: %s", exc)

    # Ensure tables exist
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed demo project configurations
    async with AsyncSessionLocal() as session:
        try:
            await seed_demo_project(session)
            await session.commit()
        except Exception as exc:
            logger.warning("Seed error: %s", exc)
            await session.rollback()

    logger.info("=== Application startup complete ===")
    yield
    logger.info("=== GreenSynth Analytics shutting down ===")


# ── Create FastAPI application ─────────────────────────────
app = FastAPI(
    title="GreenSynth Analytics API",
    description=(
        "Data-Driven Experimental Analysis and Optimization System "
        "for Green Synthesis of Semiconductor Materials.\n\n"
        "**Scientific principle:** All calculated results are traceable "
        "to raw data + method + formula. Measured, calculated, predicted, "
        "and validated values are never mixed."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS Middleware ────────────────────────────────────────
# Uses allow_origin_regex to match all Vercel deployments (*.vercel.app) and localhost ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ─────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle validation errors raised in services."""
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error_code": "VALIDATION_ERROR", "message": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Logs the full error and returns a generic 500 response.
    The actual error message is not exposed to clients in production.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    detail = str(exc) if settings.debug else "An internal error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error_code": "INTERNAL_ERROR", "message": detail},
    )


# ── Include Routers ────────────────────────────────────────
from app.api.routes import (  # noqa: E402
    analysis,
    analytics,
    characterizations,
    dashboard,
    doe,
    evidence,
    experiments,
    files,
    health,
    integrity,
    ml,
    optimization,
    parameters,
    project_config,
    projects,
    recommendations,
    reports,
    samples,
    validation,
)

API_PREFIX = "/api/v1"

app.include_router(health.router)               # /health, /health/db
app.include_router(project_config.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(experiments.router, prefix=API_PREFIX)
app.include_router(samples.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(parameters.router, prefix=API_PREFIX)
app.include_router(characterizations.router, prefix=API_PREFIX)
app.include_router(files.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(doe.router, prefix=API_PREFIX)
app.include_router(ml.router, prefix=API_PREFIX)
app.include_router(validation.router, prefix=API_PREFIX)
app.include_router(recommendations.router, prefix=API_PREFIX)
app.include_router(evidence.router, prefix=API_PREFIX)
app.include_router(optimization.router, prefix=API_PREFIX)
app.include_router(integrity.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)


# ── Root redirect ──────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api": API_PREFIX,
    }
