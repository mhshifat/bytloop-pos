"""Donations — non-profit gifts, tax receipts, campaign totals."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Campaign(Base):
    __tablename__ = "donation_campaigns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_donation_campaign_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    goal_cents: Mapped[int] = mapped_column(default=0)
    starts_on: Mapped[date | None] = mapped_column(Date, default=None)
    ends_on: Mapped[date | None] = mapped_column(Date, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Donation(Base):
    __tablename__ = "donations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "receipt_no", name="uq_donation_receipt_no"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(String(3), default="BDT")
    campaign: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    # Overrides the customer's display name on the receipt — used for
    # honor-of / memory-of gifts.
    donor_name_override: Mapped[str | None] = mapped_column(String(255), default=None)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    receipt_no: Mapped[str] = mapped_column(String(32), default="")
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
