"""Consignment — consignors, their items, and payout history.

Three tables:

* ``consignors`` — the people who drop things off. Carries a running
  ``balance_cents`` (accrued-but-unpaid) so we don't need to sum the item
  table on every read. Reconcilable by summing ``sold`` items minus payouts.
* ``consignment_items`` — one per physical item; status goes
  ``listed -> sold | returned``. ``consignor_share_cents`` is frozen at
  sale time so a later payout-rate change doesn't rewrite history.
* ``consignor_payouts`` — append-only audit of money leaving the shop.

Audit-table pattern is used (vs a JSON blob on the consignor row) because
payout disputes are the #1 reason thrift shops get sued; each row has its
own PK + timestamp and is trivially exportable for a 1099-MISC run.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ConsignmentItemStatus(StrEnum):
    LISTED = "listed"
    SOLD = "sold"
    RETURNED = "returned"


class Consignor(Base):
    __tablename__ = "consignors"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    phone: Mapped[str | None] = mapped_column(String(32), default=None)
    # Numeric so 33.333% doesn't quietly become a float rounding bug. Two
    # decimal places is plenty — nobody consigns at 60.001%.
    payout_rate_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=50.0)
    balance_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ConsignmentItem(Base):
    __tablename__ = "consignment_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    consignor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consignors.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ConsignmentItemStatus] = mapped_column(
        String(16), default=ConsignmentItemStatus.LISTED
    )
    listed_price_cents: Mapped[int] = mapped_column(default=0)
    listed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    sold_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    sold_price_cents: Mapped[int | None] = mapped_column(default=None)
    consignor_share_cents: Mapped[int | None] = mapped_column(default=None)
    # Keep a link to the sale so refunds can reverse the share cleanly.
    sold_order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )


class ConsignorPayout(Base):
    """Append-only audit row — each payout is one row, no updates."""

    __tablename__ = "consignor_payouts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    consignor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consignors.id", ondelete="CASCADE"),
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(default=0)
    # Snapshot the consignor balance *after* the payout so reconstructing a
    # ledger is a simple ORDER BY created_at without replaying every event.
    balance_after_cents: Mapped[int] = mapped_column(default=0)
    note: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
