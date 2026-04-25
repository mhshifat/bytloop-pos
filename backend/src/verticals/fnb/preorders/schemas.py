from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.modules.sales.entity import PaymentMethod
from src.verticals.fnb.preorders.entity import PreorderStatus


class PreorderItemInput(CamelModel):
    product_id: UUID
    quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)


class PreorderItemRead(CamelModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price_cents: int


class PreorderCreate(CamelModel):
    customer_id: UUID | None = None
    pickup_at: datetime
    notes: str | None = Field(default=None, max_length=1024)
    items: list[PreorderItemInput] = Field(min_length=1)


class PreorderRead(CamelModel):
    id: UUID
    customer_id: UUID | None
    pickup_at: datetime
    status: PreorderStatus
    order_id: UUID | None
    notes: str | None
    total_cents: int
    items: list[PreorderItemRead] = []


class UpdatePreorderStatusRequest(CamelModel):
    status: PreorderStatus


class ConvertToOrderRequest(CamelModel):
    payment_method: PaymentMethod = PaymentMethod.CASH
    amount_tendered_cents: int | None = None
    payment_reference: str | None = None


class ListForDayQuery(CamelModel):
    day: date
