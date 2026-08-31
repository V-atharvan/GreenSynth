"""
GreenSynth Analytics — Group Membership ORM Model

Connects users to research groups. Defines leadership role (is_leader=True/False)
without introducing a global administrative hierarchy.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MembershipStatus(str, enum.Enum):
    """Status of user membership within a research group."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REMOVED = "REMOVED"


class GroupMembership(Base):
    """
    Group membership association.

    Maps a User to a ResearchGroup. Enforces uniqueness so a user
    cannot be added to the same group multiple times.
    """

    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_membership_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_leader: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MembershipStatus.ACTIVE.value,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
    group: Mapped["ResearchGroup"] = relationship(  # type: ignore[name-defined]
        "ResearchGroup", back_populates="memberships"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="group_memberships"
    )

    def __repr__(self) -> str:
        return (
            f"<GroupMembership id={self.id!s} group_id={self.group_id!s} "
            f"user_id={self.user_id!s} is_leader={self.is_leader}>"
        )
