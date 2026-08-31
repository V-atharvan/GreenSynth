"""
GreenSynth Analytics — Research Group ORM Model

Represents one student research group assigned to one synthesis project.
Connects users (via GroupMembership) to the project entity (projects.id).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GroupStatus(str, enum.Enum):
    """Lifecycle status of a student research group."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"


class ResearchGroup(Base):
    """
    Research group record.

    A research group consists of a Group Leader and student members
    collaborating on a specific synthesis project (P1–P8).
    """

    __tablename__ = "research_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    leader_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=GroupStatus.ACTIVE.value,
        index=True,
    )

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
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="research_groups"
    )
    leader: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="led_research_groups", foreign_keys=[leader_user_id]
    )
    memberships: Mapped[list["GroupMembership"]] = relationship(  # type: ignore[name-defined]
        "GroupMembership", back_populates="group", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(  # type: ignore[name-defined]
        "Invitation", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ResearchGroup id={self.id!s} name={self.name!r} project_id={self.project_id!s}>"
