from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.retail.furniture.entity import CustomOrderStatus


class CustomOrderRead(CamelModel):
    id: UUID
    product_id: UUID
    description: str
    quoted_price_cents: int
    customer_id: UUID | None = None
    dimensions_cm: str | None = None
    material: str | None = None
    finish: str | None = None
    status: CustomOrderStatus
    estimated_ready_on: date | None = None
    order_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class QuoteRequest(CamelModel):
    product_id: UUID
    description: str = Field(min_length=1, max_length=4096)
    quoted_price_cents: int = Field(ge=0)
    customer_id: UUID | None = None
    dimensions_cm: str | None = Field(default=None, max_length=64)
    material: str | None = Field(default=None, max_length=128)
    finish: str | None = Field(default=None, max_length=128)
    estimated_ready_on: date | None = None


class UpdateQuoteRequest(CamelModel):
    description: str | None = Field(default=None, min_length=1, max_length=4096)
    quoted_price_cents: int | None = Field(default=None, ge=0)
    dimensions_cm: str | None = Field(default=None, max_length=64)
    material: str | None = Field(default=None, max_length=128)
    finish: str | None = Field(default=None, max_length=128)
    estimated_ready_on: date | None = None


class StartProductionRequest(CamelModel):
    estimated_ready_on: date | None = None


class MarkDeliveredRequest(CamelModel):
    # Linking an order is optional — shops that take cash-on-delivery may not
    # have created the order row until the piece is dropped off.
    order_id: UUID | None = None


class CancelRequest(CamelModel):
    reason: str | None = Field(default=None, max_length=255)
