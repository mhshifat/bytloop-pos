from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.correlation import get_correlation_id
from src.modules.audit.entity import AuditEvent


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before=before,
            after=after,
            correlation_id=get_correlation_id() or None,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list(
        self,
        *,
        tenant_id: UUID,
        resource_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditEvent], bool]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.created_at.desc())
        )
        if resource_type:
            stmt = stmt.where(AuditEvent.resource_type == resource_type)
        stmt = stmt.limit(limit + 1).offset(offset)
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more
