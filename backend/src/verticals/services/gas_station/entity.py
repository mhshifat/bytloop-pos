"""Gas station — dispensers and totalizer readings."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class FuelType(StrEnum):
    REGULAR = "regular"
    PREMIUM = "premium"
    DIESEL = "diesel"
    CNG = "cng"


class DispenserStatus(StrEnum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"


class FuelDispenser(Base):
    __tablename__ = "fuel_dispensers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "label", name="uq_fuel_dispenser_label"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(32))
    fuel_type: Mapped[FuelType] = mapped_column(String(16))
    price_per_liter_cents: Mapped[int] = mapped_column(default=0)
    # The catalog product that represents a litre of this fuel — lets the sales
    # service create properly-tracked orders through the normal checkout path.
    product_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        default=None,
    )
    status: Mapped[DispenserStatus] = mapped_column(
        String(16), default=DispenserStatus.ACTIVE
    )


class DispenserReading(Base):
    """Cumulative totalizer snapshot — the classic odometer-style meter."""

    __tablename__ = "fuel_dispenser_readings"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    dispenser_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fuel_dispensers.id", ondelete="CASCADE"),
        index=True,
    )
    # Stored as numeric so rounding-to-integer-liters happens in the order
    # quantity only — we keep true decimal litres on the reading audit trail.
    totalizer_reading: Mapped[float] = mapped_column(Numeric(14, 3))
    liters_dispensed: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
    )
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
