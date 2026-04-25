from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.specialty.cinema.entity import SeatStatus


class ShowRead(CamelModel):
    id: UUID
    title: str
    screen: str
    starts_at: datetime
    ends_at: datetime
    ticket_price_cents: int


class SeatRead(CamelModel):
    id: UUID
    show_id: UUID
    label: str
    status: SeatStatus
    held_until: datetime | None = None


class ShowCreate(CamelModel):
    title: str = Field(min_length=1, max_length=255)
    screen: str = Field(min_length=1, max_length=32)
    starts_at: datetime
    ends_at: datetime
    ticket_price_cents: int = Field(ge=0)
    # Either explicit labels or a rows/cols grid.
    seat_labels: list[str] | None = None
    seat_map_rows: int | None = Field(default=None, ge=1, le=50)
    seat_map_cols: int | None = Field(default=None, ge=1, le=50)


class HoldSeatRequest(CamelModel):
    held_by: str = Field(min_length=1, max_length=64)
    ttl_seconds: int = Field(default=600, ge=30, le=3600)


class ReleaseSeatRequest(CamelModel):
    held_by: str = Field(min_length=1, max_length=64)


class SellSeatRequest(CamelModel):
    order_id: UUID | None = None
    held_by: str | None = None
