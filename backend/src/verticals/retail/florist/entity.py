"""Florist — bouquet templates, components, and composed instances.

Four tables, split because the lifecycle of a *template* (catalog-ish,
edited rarely) is different from an *instance* (one per sale, immutable
once composed):

* ``bouquet_templates`` — reusable recipes (the "Classic Dozen Roses" the
  shop sells every day). ``code`` is unique per tenant so staff can punch
  it in at the counter.
* ``bouquet_components`` — the default line items on a template. We store
  ``component_name`` as a string rather than FK-ing to ``products``
  because a "Red rose" stem is often tracked by bunch, not SKU, and we
  don't want to force every stem into the catalog.
* ``bouquet_instances`` — one row per bouquet actually built. ``template_id``
  is nullable to support fully bespoke compositions. ``total_price_cents``
  is snapshotted at compose time so a later template price change doesn't
  retroactively rewrite sales history.
* ``bouquet_instance_items`` — the frozen line items for that instance;
  copied from the template (or passed in for bespoke) so edits to the
  template don't touch delivered bouquets.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class BouquetTemplate(Base):
    __tablename__ = "bouquet_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "code", name="uq_bouquet_templates_tenant_code"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    base_price_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class BouquetComponent(Base):
    __tablename__ = "bouquet_components"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bouquet_templates.id", ondelete="CASCADE"),
        index=True,
    )
    component_name: Mapped[str] = mapped_column(String(128))
    default_quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cents: Mapped[int] = mapped_column(default=0)


class BouquetInstance(Base):
    __tablename__ = "bouquet_instances"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    total_price_cents: Mapped[int] = mapped_column(default=0)
    # Nullable — bespoke bouquets (customer picked stems at the counter) have
    # no originating template. SET NULL would also be acceptable but CASCADE
    # feels wrong; we choose to keep the history even if the template is
    # deleted, so a soft reference via nullable FK with SET NULL.
    template_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bouquet_templates.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    # Linked at sale time; SET NULL so refund-then-purge of orders leaves the
    # bouquet composition searchable for "did we send out X roses last week?".
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    wrap_style: Mapped[str | None] = mapped_column(String(64), default=None)
    card_message: Mapped[str | None] = mapped_column(Text, default=None)
    delivery_schedule_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_schedules.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class BouquetInstanceItem(Base):
    __tablename__ = "bouquet_instance_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bouquet_instances.id", ondelete="CASCADE"),
        index=True,
    )
    component_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cents: Mapped[int] = mapped_column(default=0)
