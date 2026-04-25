from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.fnb.qsr.entity import DriveThruStatus


class CreateTicketRequest(CamelModel):
    order_id: UUID
    lane: str | None = Field(default=None, max_length=32)
    estimated_ready_at: datetime | None = None


class DriveThruTicketRead(CamelModel):
    id: UUID
    order_id: UUID
    call_number: int
    status: DriveThruStatus
    lane: str | None
    estimated_ready_at: datetime | None
    called_at: datetime | None
    served_at: datetime | None
    created_at: datetime


class BoardRead(CamelModel):
    """Customer-display board — active tickets grouped by status."""

    ordering: list[DriveThruTicketRead] = []
    preparing: list[DriveThruTicketRead] = []
    ready: list[DriveThruTicketRead] = []
