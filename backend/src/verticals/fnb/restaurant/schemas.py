from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.fnb.restaurant.entity import KdsStation, KotStatus, TableStatus


class TableRead(CamelModel):
    id: UUID
    code: str
    label: str
    seats: int
    status: TableStatus
    current_order_id: UUID | None


class TableCreate(CamelModel):
    code: str = Field(min_length=1, max_length=16)
    label: str = Field(min_length=1, max_length=64)
    seats: int = Field(default=4, ge=1, le=40)


class KotItemInput(CamelModel):
    product_id: UUID
    name_snapshot: str
    quantity: int = Field(ge=1)
    modifier_notes: str | None = None


class FireKotRequest(CamelModel):
    order_id: UUID
    station: KdsStation
    items: list[KotItemInput] = Field(min_length=1)
    course: int = Field(default=1, ge=1, le=9)


class FireOrderRequest(CamelModel):
    """Auto-route all items to their configured stations."""

    order_id: UUID
    items: list[KotItemInput] = Field(min_length=1)


class KotTicketRead(CamelModel):
    id: UUID
    order_id: UUID
    number: str
    station: KdsStation
    status: KotStatus
    course: int = 1
    fired_at: datetime
    ready_at: datetime | None


class UpdateKotStatusRequest(CamelModel):
    status: KotStatus


class RouteUpsertRequest(CamelModel):
    product_id: UUID
    station: KdsStation
    course: int = Field(default=1, ge=1, le=9)


class RouteRead(CamelModel):
    id: UUID
    product_id: UUID
    station: KdsStation
    course: int
