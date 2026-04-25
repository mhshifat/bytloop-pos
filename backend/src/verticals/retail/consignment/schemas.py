from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.retail.consignment.entity import ConsignmentItemStatus


class ConsignorRead(CamelModel):
    id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    payout_rate_pct: float
    balance_cents: int
    created_at: datetime


class CreateConsignorRequest(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    payout_rate_pct: float = Field(default=50.0, ge=0.0, le=100.0)


class ConsignmentItemRead(CamelModel):
    id: UUID
    consignor_id: UUID
    product_id: UUID
    status: ConsignmentItemStatus
    listed_price_cents: int
    listed_at: datetime
    sold_at: datetime | None = None
    sold_price_cents: int | None = None
    consignor_share_cents: int | None = None
    sold_order_id: UUID | None = None


class AddItemRequest(CamelModel):
    consignor_id: UUID
    product_id: UUID
    listed_price_cents: int = Field(ge=0)


class MarkSoldRequest(CamelModel):
    sold_price_cents: int = Field(ge=0)
    order_id: UUID


class PayoutRequest(CamelModel):
    amount_cents: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)


class ConsignorPayoutRead(CamelModel):
    id: UUID
    consignor_id: UUID
    amount_cents: int
    balance_after_cents: int
    note: str | None = None
    created_at: datetime
