"""Cannabis retail — METRC-compatible batch tracking + sales ledger.

The ledger (`CannabisTransaction`) is the legal source of truth that flows to
METRC. It is append-only: every state change (receive / sell / destroy / recall)
becomes a new row. `PurchaseLimit` tracks daily per-customer grams to enforce
jurisdictional possession caps at the sell-call site.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class BatchState(StrEnum):
    RECEIVED = "received"
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    RECALLED = "recalled"


class TransactionKind(StrEnum):
    RECEIVED = "received"
    SOLD = "sold"
    ADJUSTED = "adjusted"
    DESTROYED = "destroyed"
    RECALLED = "recalled"


class MetrcSyncStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class CannabisBatch(Base):
    __tablename__ = "cannabis_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "batch_id", name="uq_cannabis_batch_tag"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # The external METRC tag — unique per tenant, supplied by the grower/processor.
    batch_id: Mapped[str] = mapped_column(String(64))
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    strain_name: Mapped[str] = mapped_column(String(128))
    harvested_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date] = mapped_column(Date)
    quantity_grams: Mapped[float] = mapped_column(Numeric(12, 3))
    thc_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    cbd_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    state: Mapped[BatchState] = mapped_column(String(16), default=BatchState.RECEIVED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class CannabisTransaction(Base):
    """Append-only compliance ledger. One row per movement."""

    __tablename__ = "cannabis_transactions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cannabis_batches.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[TransactionKind] = mapped_column(String(16))
    # Signed: receive + adjust-up are positive; sell/destroy/recall/adjust-down negative.
    grams_delta: Mapped[float] = mapped_column(Numeric(12, 3))
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(String(512), default=None)
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    metrc_sync_status: Mapped[MetrcSyncStatus] = mapped_column(
        String(16), default=MetrcSyncStatus.PENDING, index=True
    )
    metrc_sync_error: Mapped[str | None] = mapped_column(String(1024), default=None)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class PurchaseLimit(Base):
    """Daily per-customer gram tally — enforces jurisdictional possession caps."""

    __tablename__ = "cannabis_purchase_limits"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "customer_id", "day_date", name="uq_cannabis_daily_limit"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    day_date: Mapped[date] = mapped_column(Date)
    grams_purchased: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
