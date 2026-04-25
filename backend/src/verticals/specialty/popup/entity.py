"""Pop-up / flea-market mode — ephemeral events with per-event stalls.

A ``PopupEvent`` bounds a temporary trading window. ``PopupStall`` is the
physical booth slot (one operator per). ``PopupInventorySnapshot`` is
taken at open/close so the event produces a clean sold-quantity delta
without touching the long-lived inventory ledger.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PopupEvent(Base):
    __tablename__ = "popup_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_popup_events_tenant_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_notes: Mapped[str | None] = mapped_column(String(1024), default=None)


class PopupStall(Base):
    __tablename__ = "popup_stalls"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("popup_events.id", ondelete="CASCADE"),
        index=True,
    )
    stall_label: Mapped[str] = mapped_column(String(64))
    # SET NULL: if the operator user is deleted, keep the stall row around
    # so sold-quantity attribution survives for reporting.
    operator_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )


class PopupInventorySnapshot(Base):
    """Opening (and later closing) stock level for a tracked product.

    One row per (event, product). ``closing_stock`` stays NULL until the
    event is torn down; the sold-count is ``opening - closing`` at that
    point.
    """

    __tablename__ = "popup_inventory_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "product_id", name="uq_popup_snapshot_event_product"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("popup_events.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    opening_stock: Mapped[int] = mapped_column(default=0)
    closing_stock: Mapped[int | None] = mapped_column(default=None)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
