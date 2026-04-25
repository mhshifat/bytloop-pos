"""Sales entities — orders, order items, payments, receipts.

``order_type`` discriminates across verticals (retail, dine_in, takeaway,
delivery, appointment, job_card, rental...). See docs/PLAN.md §10.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class OrderType(StrEnum):
    RETAIL = "retail"
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"
    APPOINTMENT = "appointment"
    JOB_CARD = "job_card"
    RENTAL = "rental"


class OrderStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    VOIDED = "voided"
    REFUNDED = "refunded"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    BKASH = "bkash"
    NAGAD = "nagad"
    SSLCOMMERZ = "sslcommerz"
    ROCKET = "rocket"
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), index=True
    )
    number: Mapped[str] = mapped_column(String(32), index=True)
    cashier_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    order_type: Mapped[OrderType] = mapped_column(String(24), default=OrderType.RETAIL)
    status: Mapped[OrderStatus] = mapped_column(String(16), default=OrderStatus.OPEN)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    subtotal_cents: Mapped[int] = mapped_column(default=0)
    tax_cents: Mapped[int] = mapped_column(default=0)
    discount_cents: Mapped[int] = mapped_column(default=0)
    total_cents: Mapped[int] = mapped_column(default=0)
    vertical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default_factory=dict)

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    name_snapshot: Mapped[str] = mapped_column(String(255))
    unit_price_cents: Mapped[int] = mapped_column(default=0)
    quantity: Mapped[int] = mapped_column(default=1)
    subtotal_cents: Mapped[int] = mapped_column(default=0)
    tax_cents: Mapped[int] = mapped_column(default=0)
    line_total_cents: Mapped[int] = mapped_column(default=0)
    vertical_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default_factory=dict)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    method: Mapped[PaymentMethod] = mapped_column(String(24))
    amount_cents: Mapped[int] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    reference: Mapped[str | None] = mapped_column(String(128), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
