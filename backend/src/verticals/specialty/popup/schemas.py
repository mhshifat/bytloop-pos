from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class PopupEventRead(CamelModel):
    id: UUID
    code: str
    name: str
    venue: str
    starts_at: datetime
    ends_at: datetime
    location_notes: str | None = None


class PopupEventCreate(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    venue: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime
    location_notes: str | None = Field(default=None, max_length=1024)


class PopupStallRead(CamelModel):
    id: UUID
    event_id: UUID
    stall_label: str
    operator_user_id: UUID | None = None


class PopupStallCreate(CamelModel):
    event_id: UUID
    stall_label: str = Field(min_length=1, max_length=64)
    operator_user_id: UUID | None = None


class PopupInventorySnapshotRead(CamelModel):
    id: UUID
    event_id: UUID
    product_id: UUID
    opening_stock: int
    closing_stock: int | None = None
    opened_at: datetime
    closed_at: datetime | None = None


class PopupSoldLine(CamelModel):
    product_id: UUID
    opening_stock: int
    closing_stock: int
    sold_count: int


class PopupCloseReport(CamelModel):
    event_id: UUID
    lines: list[PopupSoldLine]
    total_sold_units: int
