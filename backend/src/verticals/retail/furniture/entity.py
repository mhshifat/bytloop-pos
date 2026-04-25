"""Furniture — made-to-order workflow.

One ``CustomOrder`` per bespoke request (a custom sofa, a kitchen counter cut
to size, a built-in bookshelf). The row lives through its own lifecycle —
``quoted -> in_production -> ready -> delivered`` (or ``cancelled``) — and
only gets linked to an ``orders`` row when the customer actually pays. That
late binding matters: a shop quotes many jobs that never convert, and we
don't want an ``order`` dangling for every dead lead.

The customer FK uses ``SET NULL`` so purging a customer (GDPR, merge) leaves
the production history intact; ``product_id`` (the base catalog SKU being
customized) is ``RESTRICT`` because losing the base product silently would
leave dimensions/material referring to nothing.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class CustomOrderStatus(StrEnum):
    QUOTED = "quoted"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CustomOrder(Base):
    __tablename__ = "furniture_custom_orders"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # The base catalog product being customized. RESTRICT — if someone deletes
    # the "Two-seater sofa frame" SKU we want the delete to fail loudly rather
    # than orphan every in-production job that was quoted from it.
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    quoted_price_cents: Mapped[int] = mapped_column(default=0)
    # SET NULL on customer — we keep production history even if the customer
    # row is purged (GDPR merge, duplicate cleanup).
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    # Free-form "200x90x75" rather than a structured triple — kitchen counters
    # take L-shapes, round tables take just a diameter, and we don't want to
    # invent a column per shape.
    dimensions_cm: Mapped[str | None] = mapped_column(String(64), default=None)
    material: Mapped[str | None] = mapped_column(String(128), default=None)
    finish: Mapped[str | None] = mapped_column(String(128), default=None)
    status: Mapped[CustomOrderStatus] = mapped_column(
        String(16), default=CustomOrderStatus.QUOTED, index=True
    )
    estimated_ready_on: Mapped[date | None] = mapped_column(Date, default=None)
    # Linked only once the customer pays. SET NULL so a purged order (audit
    # cleanup) still leaves the custom-order trail readable.
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )
