"""Bar tabs — open-until-close running tabs with card pre-auth.

A bartender opens a tab tied to a customer (or walk-in) with an opaque
payment-gateway pre-auth reference, adds drinks across the shift, and then
closes the tab. Close time runs a full sales checkout against the accumulated
lines and flips the tab to CLOSED.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class BarTabStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    ABANDONED = "abandoned"


class BarTab(Base):
    __tablename__ = "bar_tabs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    opened_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[BarTabStatus] = mapped_column(String(16), default=BarTabStatus.OPEN)
    # Opaque handle from the payment gateway (e.g. Stripe payment_intent id,
    # bKash trxID) that was pre-authorized when the tab opened.
    preauth_reference: Mapped[str | None] = mapped_column(String(128), default=None)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    total_cents: Mapped[int] = mapped_column(default=0)


class BarTabLine(Base):
    __tablename__ = "bar_tab_lines"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    tab_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bar_tabs.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT")
    )
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cents: Mapped[int] = mapped_column(default=0)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
