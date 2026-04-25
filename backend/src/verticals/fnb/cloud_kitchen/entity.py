"""Cloud kitchen — virtual-brand routing for ghost kitchens.

One physical kitchen fulfils orders for multiple delivery-only brands.
``VirtualBrand`` is a tenant-scoped branding identity, ``BrandProduct``
is the many-to-many join to ``products``, and ``BrandOrder`` audits
which brand a sales order was tagged to.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class VirtualBrand(Base):
    __tablename__ = "virtual_brands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_virtual_brands_tenant_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    logo_url: Mapped[str | None] = mapped_column(String(512), default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class BrandProduct(Base):
    """Association between a virtual brand and a product.

    Composite PK on (brand_id, product_id) so the same product can be
    sold under multiple brands without duplication.
    """

    __tablename__ = "brand_products"

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    brand_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("virtual_brands.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class BrandOrder(Base):
    """Audit row tagging a sales order to the brand it was placed under."""

    __tablename__ = "brand_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_id", name="uq_brand_orders_tenant_order"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    # RESTRICT — deleting a brand with historical orders should fail so
    # we preserve the audit trail (soft-delete the brand via is_active).
    brand_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("virtual_brands.id", ondelete="RESTRICT"),
        index=True,
    )
    external_order_ref: Mapped[str | None] = mapped_column(String(128), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
