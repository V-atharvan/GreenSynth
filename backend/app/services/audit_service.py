"""
GreenSynth Analytics — Audit Service

Provides methods for recording and retrieving scientific audit trails.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service layer for audit log creation and queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        user_id: uuid.UUID | None = None,
        changes: dict | None = None,
        notes: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_entry = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            notes=notes,
        )
        self.db.add(audit_entry)
        await self.db.flush()
        logger.debug(
            "AuditLog recorded: [%s] %s on %s",
            action, entity_type, entity_id
        )
        return audit_entry

    async def get_entity_logs(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> Sequence[AuditLog]:
        """Return all audit entries for a specific entity."""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.timestamp.desc())
        )
        return result.scalars().all()
