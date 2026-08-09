"""
GreenSynth Analytics — User ORM Model

Stores researcher/admin accounts.
Authentication is minimal in Phase 1 — full JWT auth is Phase 3.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserRole(str):
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class User(Base):
    """
    System user account.

    Roles:
      ADMIN      — manage users, configure projects
      RESEARCHER — create experiments, upload data, analyse
      VIEWER     — read-only access to results and reports
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="RESEARCHER"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s} username={self.username!r} role={self.role!r}>"
