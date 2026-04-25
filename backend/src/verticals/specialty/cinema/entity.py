"""Cinema — shows + reserved seats."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class SeatStatus(StrEnum):
    AVAILABLE = "available"
    HELD = "held"
    SOLD = "sold"


class Show(Base):
    __tablename__ = "cinema_shows"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    screen: Mapped[str] = mapped_column(String(32))
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    ticket_price_cents: Mapped[int] = mapped_column(default=0)


class Seat(Base):
    __tablename__ = "cinema_seats"
    __table_args__ = (UniqueConstraint("show_id", "label", name="uq_cinema_seat"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    show_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cinema_shows.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(8))
    status: Mapped[SeatStatus] = mapped_column(String(16), default=SeatStatus.AVAILABLE)
    # While a seat is HELD, this is the customer/session identifier that may
    # convert it to SOLD. Cleared when the hold expires or the sale completes.
    held_by: Mapped[str | None] = mapped_column(String(64), default=None)
    held_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
    )
