"""RFID memberships — wristband / card passes for car-wash, theme-park, etc."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PassStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class RfidPass(Base):
    __tablename__ = "rfid_passes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rfid_tag", name="uq_rfid_pass_tag"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    rfid_tag: Mapped[str] = mapped_column(String(64))
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    plan_code: Mapped[str] = mapped_column(String(64), default="")
    # ``balance_uses`` is for punch-style passes (N redemptions); ``expires_on``
    # is for time-based passes. A plan may use either or both depending on how
    # the venue sells it.
    balance_uses: Mapped[int | None] = mapped_column(default=None)
    expires_on: Mapped[date | None] = mapped_column(Date, default=None)
    status: Mapped[PassStatus] = mapped_column(String(16), default=PassStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class PassUse(Base):
    """Log row written each time a pass is redeemed (or attempted)."""

    __tablename__ = "rfid_pass_uses"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    pass_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rfid_passes.id", ondelete="CASCADE"), index=True
    )
    location: Mapped[str] = mapped_column(String(64), default="")
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
