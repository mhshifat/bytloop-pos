from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.specialty.tickets.entity import EventStatus, TicketStatus


class EventCreate(CamelModel):
    title: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime
    venue: str = Field(default="", max_length=255)


class EventRead(CamelModel):
    id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    venue: str
    status: EventStatus


class TicketTypeCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    price_cents: int = Field(ge=0)
    quota: int = Field(ge=0)


class TicketTypeRead(CamelModel):
    id: UUID
    event_id: UUID
    code: str
    name: str
    price_cents: int
    quota: int
    sold_count: int


class PurchaseTicketsRequest(CamelModel):
    ticket_type_id: UUID
    quantity: int = Field(ge=1, le=200)
    order_id: UUID | None = None
    holder_names: list[str] = Field(default_factory=list)


class IssuedTicketRead(CamelModel):
    id: UUID
    ticket_type_id: UUID
    order_id: UUID | None = None
    holder_name: str
    serial_no: str
    status: TicketStatus
    scanned_at: datetime | None = None
    issued_at: datetime


class ScanRequest(CamelModel):
    serial_no: str = Field(min_length=1, max_length=64)


class VoidRequest(CamelModel):
    serial_no: str = Field(min_length=1, max_length=64)
