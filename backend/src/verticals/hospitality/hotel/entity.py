"""Hotel — rooms + reservations."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ReservationStatus(StrEnum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class Room(Base):
    __tablename__ = "hotel_rooms"
    __table_args__ = (UniqueConstraint("tenant_id", "number", name="uq_rooms_tenant_number"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(32), default="standard")
    nightly_rate_cents: Mapped[int] = mapped_column(default=0)


class Reservation(Base):
    __tablename__ = "hotel_reservations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("hotel_rooms.id", ondelete="RESTRICT"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    status: Mapped[ReservationStatus] = mapped_column(String(16), default=ReservationStatus.BOOKED)
    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    checked_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class FolioCharge(Base):
    """Incidental charges posted to a reservation (room service, laundry, bar)."""

    __tablename__ = "hotel_folio_charges"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    reservation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hotel_reservations.id", ondelete="CASCADE"),
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255))
    amount_cents: Mapped[int] = mapped_column(default=0)
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
