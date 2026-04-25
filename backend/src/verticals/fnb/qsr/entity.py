"""QSR — drive-thru / takeaway queue with called-number display.

Each ticket gets a short ``call_number`` that is unique per tenant per
day (UTC). The number is announced on a customer-facing display board
so guests can collect when their number lights up.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class DriveThruStatus(StrEnum):
    ORDERING = "ordering"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    ABANDONED = "abandoned"


class DriveThruTicket(Base):
    __tablename__ = "drive_thru_tickets"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    # Sequential per tenant per day (UTC), rolls over at midnight UTC.
    call_number: Mapped[int] = mapped_column()
    status: Mapped[DriveThruStatus] = mapped_column(
        String(16), default=DriveThruStatus.ORDERING
    )
    lane: Mapped[str | None] = mapped_column(String(32), default=None)
    estimated_ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    called_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    served_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
