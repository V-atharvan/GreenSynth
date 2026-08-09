"""
GreenSynth Analytics — SQLAlchemy Declarative Base
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base.

    All ORM model classes inherit from this Base.
    """

    pass
