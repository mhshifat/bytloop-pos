"""Discounts + promotions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class DiscountKind(StrEnum):
    PERCENT = "percent"
    FIXED = "fixed"


class Discount(Base):
    __tablename__ = "discounts"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_discounts_tenant_code"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    kind: Mapped[DiscountKind] = mapped_column(String(16))
    percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), default=None)
    amount_cents: Mapped[int | None] = mapped_column(default=None)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class DiscountHelpers:
    @staticmethod
    def apply(discount: Discount, subtotal_cents: int) -> int:
        """Returns the discount amount to subtract from subtotal (non-negative)."""
        if discount.kind == DiscountKind.PERCENT and discount.percent is not None:
            return int(subtotal_cents * float(discount.percent))
        if discount.kind == DiscountKind.FIXED and discount.amount_cents is not None:
            return min(discount.amount_cents, subtotal_cents)
        return 0
