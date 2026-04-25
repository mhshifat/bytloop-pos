from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class ElectronicsItemRead(CamelModel):
    id: UUID
    product_id: UUID
    serial_no: str
    imei: str | None = None
    warranty_months: int = 0
    purchased_on: date | None = None
    sold_order_id: UUID | None = None
    sold_at: datetime | None = None


class RegisterItemRequest(CamelModel):
    product_id: UUID
    serial_no: str = Field(min_length=1, max_length=128)
    imei: str | None = Field(default=None, max_length=32)
    warranty_months: int = Field(default=0, ge=0, le=600)
    purchased_on: date | None = None


class MarkSoldRequest(CamelModel):
    order_id: UUID


class WarrantyStatus(CamelModel):
    serial_no: str
    covered: bool
    # Days remaining can be negative when the warranty has lapsed — we leave
    # that to the caller to display as "expired X days ago" if desired.
    days_remaining: int
    warranty_expires_on: date | None = None
