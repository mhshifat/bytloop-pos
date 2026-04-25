"""Rental — asset catalog + rental contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class RentalStatus(StrEnum):
    RESERVED = "reserved"
    OUT = "out"
    RETURNED = "returned"
    OVERDUE = "overdue"


class RentalAsset(Base):
    __tablename__ = "rental_assets"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_rental_asset_code"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(128))
    hourly_rate_cents: Mapped[int] = mapped_column(default=0)
    daily_rate_cents: Mapped[int] = mapped_column(default=0)


class RentalContract(Base):
    __tablename__ = "rental_contracts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("rental_assets.id", ondelete="RESTRICT"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[RentalStatus] = mapped_column(String(16), default=RentalStatus.RESERVED)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deposit_cents: Mapped[int] = mapped_column(default=0)
    # Populated on return — charged back to customer on top of base rental.
    late_fee_cents: Mapped[int] = mapped_column(default=0)
    damage_fee_cents: Mapped[int] = mapped_column(default=0)
    damage_notes: Mapped[str | None] = mapped_column(String(2048), default=None)
