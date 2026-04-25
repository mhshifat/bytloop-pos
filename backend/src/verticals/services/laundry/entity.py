"""Laundry — garment drop-off / pickup ticket tracking."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class LaundryStatus(StrEnum):
    RECEIVED = "received"
    WASHING = "washing"
    READY = "ready"
    COLLECTED = "collected"
    LOST = "lost"


class LaundryTicket(Base):
    __tablename__ = "laundry_tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ticket_no", name="uq_laundry_ticket_no"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    ticket_no: Mapped[str] = mapped_column(String(32), default="")
    item_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[LaundryStatus] = mapped_column(String(16), default=LaundryStatus.RECEIVED)
    # ``order_id`` is populated at collection/payment time via mark_collected.
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
    )
    dropped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    promised_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class LaundryItem(Base):
    __tablename__ = "laundry_ticket_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laundry_tickets.id", ondelete="CASCADE"),
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    service_type: Mapped[str] = mapped_column(String(64), default="")
    price_cents: Mapped[int] = mapped_column(default=0)
