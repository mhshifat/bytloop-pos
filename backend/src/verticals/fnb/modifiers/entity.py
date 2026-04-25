"""Modifiers — product customization groups and options.

A ``ModifierGroup`` (e.g. "Pizza toppings", "Milk choice") owns a set of
``ModifierOption`` rows each of which carries a price delta (positive or
negative cents). Groups are attached to ``Product`` rows via the
``product_modifier_links`` association table so the same group can be reused
across many products.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ModifierGroup(Base):
    __tablename__ = "modifier_groups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_modifier_group_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    min_selections: Mapped[int] = mapped_column(default=0)
    max_selections: Mapped[int] = mapped_column(default=1)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ModifierOption(Base):
    __tablename__ = "modifier_options"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("modifier_groups.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128))
    price_cents_delta: Mapped[int] = mapped_column(default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductModifierLink(Base):
    """Association between a ``Product`` and a ``ModifierGroup`` (many-to-many).

    Composite PK on (product_id, modifier_group_id) prevents duplicate links;
    ``tenant_id`` is kept on the row for isolation-friendly querying.
    """

    __tablename__ = "product_modifier_links"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    modifier_group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("modifier_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
