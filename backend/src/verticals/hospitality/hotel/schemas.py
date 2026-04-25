from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.hospitality.hotel.entity import ReservationStatus


class RoomRead(CamelModel):
    id: UUID
    number: str
    category: str
    nightly_rate_cents: int


class RoomCreate(CamelModel):
    number: str = Field(min_length=1, max_length=16)
    category: str = "standard"
    nightly_rate_cents: int = Field(ge=0)


class ReservationRead(CamelModel):
    id: UUID
    room_id: UUID
    customer_id: UUID
    status: ReservationStatus
    check_in: date
    check_out: date
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None


class ReservationCreate(CamelModel):
    room_id: UUID
    customer_id: UUID
    check_in: date
    check_out: date


class UpdateReservationStatusRequest(CamelModel):
    status: ReservationStatus


class FolioChargeCreate(CamelModel):
    description: str = Field(min_length=1, max_length=255)
    amount_cents: int = Field(ge=0)


class FolioChargeRead(CamelModel):
    id: UUID
    reservation_id: UUID
    description: str
    amount_cents: int
    posted_at: datetime


class FolioRead(CamelModel):
    reservation_id: UUID
    nights: int
    room_total_cents: int
    incidentals_cents: int
    total_cents: int
    charges: list[FolioChargeRead]
