"""Catalog entities — products and categories.

Vertical-specific data lives in ``vertical_data: JSONB`` for lightweight
extensions, or in sibling tables (e.g., ``apparel_variant_matrix``) for
structured vertical models. See docs/PLAN.md §10.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_categories_tenant_slug"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    sku: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    barcode: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    description: Mapped[str | None] = mapped_column(String(2048), default=None)
    category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    price_cents: Mapped[int] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"))

    # Vertical-specific fields (apparel size/color, grocery weight, pharmacy batch…)
    vertical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default_factory=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class ProductHelpers:
    @staticmethod
    def display_price(product: Product) -> str:
        return f"{product.currency} {product.price_cents / 100:.2f}"
