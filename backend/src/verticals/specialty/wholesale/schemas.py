from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.specialty.wholesale.entity import InvoiceStatus


class TierRead(CamelModel):
    id: UUID
    code: str
    name: str
    discount_pct: Decimal


class TierUpsert(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class WholesaleCustomerRead(CamelModel):
    id: UUID
    customer_id: UUID
    tier_code: str | None
    credit_limit_cents: int
    credit_balance_cents: int
    net_terms_days: int
    tax_exempt: bool


class WholesaleCustomerCreate(CamelModel):
    customer_id: UUID
    tier_code: str | None = Field(default=None, max_length=32)
    credit_limit_cents: int = Field(ge=0, default=0)
    net_terms_days: int = Field(ge=0, default=30)
    tax_exempt: bool = False


class ApplyDiscountRequest(CamelModel):
    wholesale_customer_id: UUID
    subtotal_cents: int = Field(ge=0)


class ApplyDiscountResponse(CamelModel):
    subtotal_cents: int
    discount_cents: int
    discounted_cents: int
    tier_code: str | None
    discount_pct: Decimal


class InvoiceRead(CamelModel):
    id: UUID
    wholesale_customer_id: UUID
    order_id: UUID
    invoice_no: str
    issued_on: date
    due_on: date
    status: InvoiceStatus
    amount_cents: int
    paid_cents: int


class InvoiceCreate(CamelModel):
    order_id: UUID
    wholesale_customer_id: UUID
    invoice_no: str = Field(min_length=1, max_length=64)
    issued_on: date | None = None


class PaymentCreate(CamelModel):
    amount_cents: int = Field(gt=0)
    paid_on: date
    reference: str | None = Field(default=None, max_length=128)


class PaymentRead(CamelModel):
    id: UUID
    invoice_id: UUID
    amount_cents: int
    paid_on: date
    reference: str | None
