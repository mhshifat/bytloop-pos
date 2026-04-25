"""Wholesale B2B — tiered pricing, credit terms, invoice/AR ledger.

The `WholesaleCustomer.credit_balance_cents` is the live receivable: it grows
when invoices are issued (customer owes us more) and shrinks when payments
arrive. The `credit_limit_cents` cap is enforced at invoice time.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class InvoiceStatus(StrEnum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    WRITTEN_OFF = "written_off"


class WholesaleTier(Base):
    __tablename__ = "wholesale_tiers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_wholesale_tier_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class WholesaleCustomer(Base):
    __tablename__ = "wholesale_customers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "customer_id", name="uq_wholesale_customer_ref"
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
    # Free-text tier code (must match an existing WholesaleTier row for the
    # tenant). Nullable so a B2B account can exist before tiers are defined.
    tier_code: Mapped[str | None] = mapped_column(String(32), default=None)
    credit_limit_cents: Mapped[int] = mapped_column(default=0)
    # Signed; positive = customer owes us, negative = they're in credit.
    credit_balance_cents: Mapped[int] = mapped_column(default=0)
    net_terms_days: Mapped[int] = mapped_column(default=30)
    tax_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Invoice(Base):
    __tablename__ = "wholesale_invoices"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "invoice_no", name="uq_wholesale_invoice_no"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    wholesale_customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wholesale_customers.id", ondelete="RESTRICT"),
        index=True,
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), index=True
    )
    invoice_no: Mapped[str] = mapped_column(String(64))
    issued_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    status: Mapped[InvoiceStatus] = mapped_column(String(16), default=InvoiceStatus.OPEN)
    amount_cents: Mapped[int] = mapped_column(default=0)
    paid_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class InvoicePayment(Base):
    __tablename__ = "wholesale_invoice_payments"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wholesale_invoices.id", ondelete="CASCADE"),
        index=True,
    )
    paid_on: Mapped[date] = mapped_column(Date)
    amount_cents: Mapped[int] = mapped_column(default=0)
    reference: Mapped[str | None] = mapped_column(String(128), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
