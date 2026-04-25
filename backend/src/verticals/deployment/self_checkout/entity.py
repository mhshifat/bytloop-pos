"""Self-checkout — customer-driven scanning + staff-PIN finalize.

``SelfCheckoutSession`` is the shell the customer drives; ``SelfCheckoutScan``
is one barcode-scan line. Scans can be flagged (age-restricted, high-value,
unrecognized) — if any flag is set at completion time the session requires
a staff override before a sales Order is created.

``order_id`` is SET NULL on purpose: deleting an order shouldn't cascade-drop
the scan audit trail, which has its own compliance value.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class SelfCheckoutStatus(StrEnum):
    SCANNING = "scanning"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SelfCheckoutSession(Base):
    __tablename__ = "self_checkout_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    station_label: Mapped[str] = mapped_column(String(64))
    customer_identifier: Mapped[str | None] = mapped_column(String(128), default=None)
    status: Mapped[SelfCheckoutStatus] = mapped_column(
        String(24), default=SelfCheckoutStatus.SCANNING
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )


class SelfCheckoutScan(Base):
    __tablename__ = "self_checkout_scans"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("self_checkout_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    barcode: Mapped[str] = mapped_column(String(64))
    # SET NULL: a product deletion later must not orphan or blow up the
    # scan history — the barcode + unit price snapshot is still auditable.
    product_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cents: Mapped[int] = mapped_column(default=0)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    flagged_for_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str | None] = mapped_column(String(64), default=None)
