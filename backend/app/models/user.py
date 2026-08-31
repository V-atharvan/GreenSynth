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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str):
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class User(Base):
    """
    System user account.

    Roles:
      RESEARCHER — create experiments, upload data, analyse
      VIEWER     — read-only access to results and reports
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    roll_number: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
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

    # ── Relationships ──────────────────────────────────────
    group_memberships: Mapped[list["GroupMembership"]] = relationship(  # type: ignore[name-defined]
        "GroupMembership", back_populates="user", cascade="all, delete-orphan"
    )
    led_research_groups: Mapped[list["ResearchGroup"]] = relationship(  # type: ignore[name-defined]
        "ResearchGroup", back_populates="leader", foreign_keys="ResearchGroup.leader_user_id"
    )

    @property
    def account_type(self) -> str:
        """Returns the authoritative account type: ADMIN or STUDENT."""
        return "ADMIN" if self.role == UserRole.ADMIN else "STUDENT"

    @property
    def is_admin(self) -> bool:
        """Returns True if user has administrative privileges."""
        return self.role == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User id={self.id!s} email={self.email!r} role={self.role!r} account_type={self.account_type!r}>"
