"""Grocery — weighable products + PLU codes.

Weighable products compute a line total at scan time: ``weight_grams *
price_per_kg``. PLU codes map 4-digit shortcuts to products so cashiers can
enter them on a keypad instead of typing the SKU.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class SellUnit(StrEnum):
    EACH = "each"
    KG = "kg"
    G = "g"
    LB = "lb"


class GrocerySku(Base):
    """Weighable metadata for a product."""

    __tablename__ = "grocery_skus"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    sell_unit: Mapped[SellUnit] = mapped_column(String(8), default=SellUnit.EACH)
    price_per_unit_cents: Mapped[int] = mapped_column(default=0)
    tare_grams: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class PluCode(Base):
    __tablename__ = "plu_codes"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_plu_tenant_code"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(8))
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
