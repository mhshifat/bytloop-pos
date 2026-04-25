"""Electronics — one row per physical unit (serial / IMEI / warranty).

Unlike apparel where a variant describes a sellable SKU class, each
``ElectronicsItem`` is a *single* piece of inventory — a phone with its own
IMEI, a laptop with its own serial number. Registration happens at receiving;
``mark_sold`` links the unit to the order it left on so warranty lookups
remain queryable long after the stock row itself is gone.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ElectronicsItem(Base):
    __tablename__ = "electronics_items"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "serial_no", name="uq_electronics_items_tenant_serial"
        ),
        UniqueConstraint(
            "tenant_id", "imei", name="uq_electronics_items_tenant_imei"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    serial_no: Mapped[str] = mapped_column(String(128), index=True)
    # IMEI is 14-15 digits but we store 32 chars to cover dual-SIM concatenation
    # and manufacturer variants. Nullable — not every electronics item is a phone.
    imei: Mapped[str | None] = mapped_column(String(32), index=True, default=None)
    warranty_months: Mapped[int] = mapped_column(default=0)
    purchased_on: Mapped[date | None] = mapped_column(Date, default=None)
    # Set when the unit leaves the store. ``SET NULL`` so we keep the warranty
    # trail even if the original order is purged.
    sold_order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    sold_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
