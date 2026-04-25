"""Jewelry — karat/weight/certification attributes and daily metal rates."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class JewelryAttribute(Base):
    __tablename__ = "jewelry_attributes"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # "gold" | "silver" | "platinum" — kept free-text for tenant flexibility.
    metal: Mapped[str] = mapped_column(String(16), default="gold")
    karat: Mapped[int] = mapped_column(default=22)
    gross_grams: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0"))
    net_grams: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0"))
    # Making charge: percent OR flat cents per gram. Pct wins if both set.
    making_charge_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    making_charge_per_gram_cents: Mapped[int] = mapped_column(default=0)
    wastage_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    stone_value_cents: Mapped[int] = mapped_column(default=0)
    certificate_no: Mapped[str | None] = mapped_column(String(64), default=None)


class DailyMetalRate(Base):
    """Today's metal price per gram — updated by the shop owner each morning."""

    __tablename__ = "jewelry_metal_rates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "metal", "karat", "effective_on", name="uq_metal_rate_day"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    metal: Mapped[str] = mapped_column(String(16))
    effective_on: Mapped[date] = mapped_column(Date)
    karat: Mapped[int] = mapped_column(default=22)
    rate_per_gram_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
