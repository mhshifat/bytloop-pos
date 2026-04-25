"""Cafe loyalty — coffee-shop style punch cards.

Buy ten coffees, get one free. Each card is a physical (or virtual)
operator-scannable card with its own ``card_code``. A "punch" is one
increment of ``punches_current``; when it hits ``punches_required`` we
roll it over to a free-item credit and reset the counter.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class LoyaltyCard(Base):
    __tablename__ = "cafe_loyalty_cards"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "card_code", name="uq_cafe_loyalty_tenant_card_code"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    card_code: Mapped[str] = mapped_column(String(64), index=True)
    punches_current: Mapped[int] = mapped_column(default=0)
    punches_required: Mapped[int] = mapped_column(default=10)
    free_items_earned: Mapped[int] = mapped_column(default=0)
    total_punches_lifetime: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )
