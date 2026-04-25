"""Delivery schedules — order-level delivery metadata.

A ``DeliverySchedule`` sits alongside an ``Order`` and tracks the courier-side
state machine: scheduled → out_for_delivery → delivered (or failed). Used by
florist, furniture, and restaurant delivery verticals.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class DeliveryStatus(StrEnum):
    SCHEDULED = "scheduled"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliverySchedule(Base):
    __tablename__ = "delivery_schedules"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    address_line1: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(128))
    postal_code: Mapped[str] = mapped_column(String(32))
    country: Mapped[str] = mapped_column(String(64))
    recipient_name: Mapped[str] = mapped_column(String(128))
    recipient_phone: Mapped[str] = mapped_column(String(32))
    address_line2: Mapped[str | None] = mapped_column(String(255), default=None)
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    delivery_fee_cents: Mapped[int] = mapped_column(default=0)
    status: Mapped[DeliveryStatus] = mapped_column(
        String(24), default=DeliveryStatus.SCHEDULED
    )
    notes: Mapped[str | None] = mapped_column(String(1024), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
