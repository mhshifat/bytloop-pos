from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.schemas import CamelModel


class AuditEventRead(CamelModel):
    id: UUID
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    correlation_id: str | None
    created_at: datetime


class AuditEventList(CamelModel):
    items: list[AuditEventRead]
    has_more: bool
    page: int
    page_size: int
