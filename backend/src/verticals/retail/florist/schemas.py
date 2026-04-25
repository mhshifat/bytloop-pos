from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class BouquetTemplateRead(CamelModel):
    id: UUID
    code: str
    name: str
    base_price_cents: int
    created_at: datetime


class CreateTemplateRequest(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    base_price_cents: int = Field(ge=0)


class BouquetComponentRead(CamelModel):
    id: UUID
    template_id: UUID
    component_name: str
    default_quantity: int
    unit_price_cents: int


class AddComponentRequest(CamelModel):
    template_id: UUID
    component_name: str = Field(min_length=1, max_length=128)
    default_quantity: int = Field(default=1, ge=1)
    unit_price_cents: int = Field(ge=0)


class BouquetInstanceItemRead(CamelModel):
    id: UUID
    instance_id: UUID
    component_name: str
    quantity: int
    unit_price_cents: int


class BouquetInstanceRead(CamelModel):
    id: UUID
    total_price_cents: int
    template_id: UUID | None = None
    order_id: UUID | None = None
    wrap_style: str | None = None
    card_message: str | None = None
    delivery_schedule_id: UUID | None = None
    created_at: datetime


class ComposeItemInput(CamelModel):
    component_name: str = Field(min_length=1, max_length=128)
    quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)


class ComposeRequest(CamelModel):
    # Provide either a template to copy, or an explicit item list for bespoke.
    template_id: UUID | None = None
    items: list[ComposeItemInput] | None = None
    wrap_style: str | None = Field(default=None, max_length=64)
    card_message: str | None = Field(default=None, max_length=2048)
    delivery_schedule_id: UUID | None = None


class LinkOrderRequest(CamelModel):
    order_id: UUID
