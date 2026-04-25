from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.services.laundry.entity import LaundryStatus


class LaundryTicketRead(CamelModel):
    id: UUID
    customer_id: UUID | None = None
    ticket_no: str
    item_count: int
    status: LaundryStatus
    order_id: UUID | None = None
    dropped_at: datetime
    promised_at: datetime | None = None
    collected_at: datetime | None = None


class LaundryTicketCreate(CamelModel):
    customer_id: UUID | None = None
    ticket_no: str = Field(min_length=1, max_length=32)
    item_count: int = Field(ge=0, default=0)
    promised_at: datetime | None = None


class LaundryItemRead(CamelModel):
    id: UUID
    ticket_id: UUID
    description: str
    quantity: int
    service_type: str
    price_cents: int


class LaundryItemCreate(CamelModel):
    description: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, default=1)
    service_type: str = Field(default="", max_length=64)
    price_cents: int = Field(ge=0)


class MarkCollectedRequest(CamelModel):
    order_id: UUID | None = None
