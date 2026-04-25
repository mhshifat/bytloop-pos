"""Shifts — cashier open/close + cash drawer reconciliation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ShiftStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), index=True
    )
    cashier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[ShiftStatus] = mapped_column(String(16), default=ShiftStatus.OPEN)
    opening_float_cents: Mapped[int] = mapped_column(default=0)
    closing_counted_cents: Mapped[int | None] = mapped_column(default=None)
    expected_cash_cents: Mapped[int | None] = mapped_column(default=None)
    variance_cents: Mapped[int | None] = mapped_column(default=None)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
