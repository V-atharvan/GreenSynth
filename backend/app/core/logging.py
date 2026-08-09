"""
GreenSynth Analytics — Logging Configuration
"""

from __future__ import annotations

import logging
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured application logging.

    Sets up a consistent log format across all loggers.
    Called once at application startup from main.py.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging configured at level: %s", log_level)


# ── Module-level logger factory ────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a module."""
    return logging.getLogger(name)
