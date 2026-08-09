"""
GreenSynth Analytics — Audit Log ORM Model

Provides scientific audit trail foundation: records user actions, timestamps,
entity changes, and scientific operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditLog(Base):
    """
    Audit log record for scientific traceability.

    Tracks creation, modification, status changes, and parameter updates.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="e.g. Project, Experiment, Sample"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="e.g. CREATE, UPDATE, ARCHIVE, STATUS_CHANGE"
    )
    changes: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="JSON representation of field changes"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog entity={self.entity_type}:{self.entity_id!s} "
            f"action={self.action!r} at={self.timestamp!s}>"
        )
