"""Hardware — bulk pricing / quantity breaks.

Hardware stores routinely sell the same SKU to DIY customers one at a time
and to contractors by the box. A ``QuantityBreak`` is one rung of a per-unit
price ladder: at the configured ``min_quantity``, the unit price drops to
``unit_price_cents``. Multiple rungs per product form the ladder; pricing a
line item picks the highest ``min_quantity`` whose threshold the cart meets.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class QuantityBreak(Base):
    __tablename__ = "quantity_breaks"
    __table_args__ = (
        # One row per (tenant, product, min_quantity) — a ladder has no
        # duplicate rungs. Enforced at the DB so concurrent ``set_breaks``
        # calls can't race in a duplicate threshold.
        UniqueConstraint(
            "tenant_id",
            "product_id",
            "min_quantity",
            name="uq_quantity_breaks_tenant_product_min",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    # "10 or more" → 10. A tier of 1 is legal and means "baseline price",
    # though callers typically omit it and rely on Product.price_cents as
    # the fallback instead.
    min_quantity: Mapped[int] = mapped_column()
    unit_price_cents: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
