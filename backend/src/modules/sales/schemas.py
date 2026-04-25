from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.modules.sales.entity import OrderStatus, OrderType, PaymentMethod


class CartItemInput(CamelModel):
    product_id: UUID
    quantity: int = Field(ge=1)
    # Serialized POS metadata: serial/IMEI, batch id, department, apparel
    # variant, etc. Persisted to ``order_items.vertical_data``.
    vertical_data: dict[str, Any] | None = None
    # Jurisdiction / liquor: excise amount for this line (cents), included in
    # line total and order totals. Validated to non-negative; caps apply in service.
    excise_cents: int | None = Field(default=None, ge=0, le=10_000_000)


class AgeVerificationCheckout(CamelModel):
    """Date-of-birth capture when the cart contains age-restricted products."""

    customer_dob: date
    # Defaults to the cart’s age-gated product ids if omitted.
    product_ids: list[UUID] | None = None


class CheckoutRequest(CamelModel):
    items: list[CartItemInput] = Field(min_length=1)
    order_type: OrderType = OrderType.RETAIL
    payment_method: PaymentMethod = PaymentMethod.CASH
    amount_tendered_cents: int | None = None
    customer_id: UUID | None = None
    discount_code: str | None = None
    # For non-cash methods: the provider's payment reference (e.g. Stripe
    # payment_intent id, bKash trxID). Saved onto the Payment row so an
    # async settlement webhook can correlate back to the order.
    payment_reference: str | None = None
    # Free-form audit payload (e.g. cannabis manifest ref). Stored on ``orders.vertical_data``.
    order_vertical_data: dict[str, Any] | None = None
    # When ``items`` include at least one age-restricted product, this is required
    # so ``AgeRestrictedService.record_verification`` can log before payment completes.
    age_verification: AgeVerificationCheckout | None = None


class OrderItemRead(CamelModel):
    id: UUID
    product_id: UUID
    name_snapshot: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int
    vertical_data: dict[str, Any] = Field(default_factory=dict)


class PaymentRead(CamelModel):
    id: UUID
    method: PaymentMethod
    amount_cents: int
    currency: str


class OrderRead(CamelModel):
    id: UUID
    number: str
    order_type: OrderType
    status: OrderStatus
    currency: str
    subtotal_cents: int
    tax_cents: int
    discount_cents: int
    total_cents: int
    customer_id: UUID | None = None
    items: list[OrderItemRead]
    payments: list[PaymentRead]
    change_due_cents: int = 0


class OrderSummary(CamelModel):
    id: UUID
    number: str
    status: OrderStatus
    order_type: OrderType
    currency: str
    total_cents: int
    opened_at: datetime
    closed_at: datetime | None


class OrderList(CamelModel):
    items: list[OrderSummary]
    has_more: bool
    page: int
    page_size: int
