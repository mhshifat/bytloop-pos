from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.logistics.deliveries.entity import DeliveryStatus


class DeliveryScheduleRead(CamelModel):
    id: UUID
    order_id: UUID
    address_line1: str
    address_line2: str | None
    city: str
    postal_code: str
    country: str
    recipient_name: str
    recipient_phone: str
    scheduled_for: datetime | None
    delivered_at: datetime | None
    delivery_fee_cents: int
    status: DeliveryStatus
    notes: str | None


class ScheduleRequest(CamelModel):
    order_id: UUID
    address_line1: str = Field(min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=128)
    postal_code: str = Field(min_length=1, max_length=32)
    country: str = Field(min_length=1, max_length=64)
    recipient_name: str = Field(min_length=1, max_length=128)
    recipient_phone: str = Field(min_length=1, max_length=32)
    scheduled_for: datetime | None = None
    delivery_fee_cents: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=1024)


class MarkFailedRequest(CamelModel):
    reason: str = Field(min_length=1, max_length=1024)


class ListScheduledQuery(CamelModel):
    day: date
