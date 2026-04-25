from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class SetLocationRequest(CamelModel):
    location_name: str = Field(min_length=1, max_length=128)
    latitude: Decimal = Field(ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal = Field(ge=Decimal("-180"), le=Decimal("180"))
    starts_at: datetime
    ends_at: datetime
    notes: str | None = Field(default=None, max_length=1024)


class TruckLocationRead(CamelModel):
    id: UUID
    location_name: str
    latitude: Decimal
    longitude: Decimal
    starts_at: datetime
    ends_at: datetime
    notes: str | None
    created_at: datetime


class DailyMenuItemInput(CamelModel):
    product_id: UUID
    daily_price_cents_override: int | None = Field(default=None, ge=0)
    sold_out: bool = False
    sort_order: int = 0


class PublishMenuRequest(CamelModel):
    menu_date: date
    notes: str | None = Field(default=None, max_length=1024)
    items: list[DailyMenuItemInput] = Field(min_length=1)


class DailyMenuItemRead(CamelModel):
    id: UUID
    menu_id: UUID
    product_id: UUID
    daily_price_cents_override: int | None
    sold_out: bool
    sort_order: int


class DailyMenuRead(CamelModel):
    id: UUID
    menu_date: date
    notes: str | None
    published_at: datetime
    items: list[DailyMenuItemRead] = []


class MarkSoldOutRequest(CamelModel):
    sold_out: bool
