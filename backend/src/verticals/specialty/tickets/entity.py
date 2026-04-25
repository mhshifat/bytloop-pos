"""Tickets — event/theme-park/museum admission sales."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class EventStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class TicketStatus(StrEnum):
    ISSUED = "issued"
    SCANNED = "scanned"
    VOIDED = "voided"


class EventInstance(Base):
    __tablename__ = "ticket_event_instances"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[EventStatus] = mapped_column(String(16), default=EventStatus.ACTIVE)


class TicketType(Base):
    __tablename__ = "ticket_types"
    __table_args__ = (
        UniqueConstraint("event_id", "code", name="uq_ticket_type_event_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ticket_event_instances.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    price_cents: Mapped[int] = mapped_column(default=0)
    quota: Mapped[int] = mapped_column(default=0)
    sold_count: Mapped[int] = mapped_column(default=0)


class IssuedTicket(Base):
    """One row per admission. ``serial_no`` is the thing scanned at the gate."""

    __tablename__ = "ticket_issued"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serial_no", name="uq_issued_ticket_serial"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ticket_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        index=True,
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
    )
    holder_name: Mapped[str] = mapped_column(String(255), default="")
    serial_no: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[TicketStatus] = mapped_column(String(16), default=TicketStatus.ISSUED)
    scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
