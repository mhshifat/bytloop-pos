"""Apparel — size/color variant matrix.

Each ``ApparelVariant`` is a sellable SKU attached to a parent product.
Keeping it in a sibling table (vs JSONB) makes barcode lookup, stock, and
reports straightforward per variant.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ApparelVariant(Base):
    __tablename__ = "apparel_variants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_apparel_variants_tenant_sku"),
        UniqueConstraint(
            "product_id", "size", "color", name="uq_apparel_variants_product_size_color"
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
    sku: Mapped[str] = mapped_column(String(64))
    size: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(32))
    barcode: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    gender: Mapped[str | None] = mapped_column(String(8), default=None)
    fit: Mapped[str | None] = mapped_column(String(32), default=None)
    material: Mapped[str | None] = mapped_column(String(64), default=None)
    price_cents_override: Mapped[int | None] = mapped_column(default=None)
    stock_quantity: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
