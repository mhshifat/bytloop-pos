from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class ModifierOptionRead(CamelModel):
    id: UUID
    group_id: UUID
    name: str
    price_cents_delta: int
    is_default: bool


class ModifierOptionCreate(CamelModel):
    name: str = Field(min_length=1, max_length=128)
    price_cents_delta: int = 0
    is_default: bool = False


class ModifierOptionUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    price_cents_delta: int | None = None
    is_default: bool | None = None


class ModifierGroupRead(CamelModel):
    id: UUID
    code: str
    name: str
    min_selections: int
    max_selections: int
    required: bool
    options: list[ModifierOptionRead] = []


class ModifierGroupCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    min_selections: int = Field(default=0, ge=0, le=50)
    max_selections: int = Field(default=1, ge=1, le=50)
    required: bool = False


class ModifierGroupUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    min_selections: int | None = Field(default=None, ge=0, le=50)
    max_selections: int | None = Field(default=None, ge=1, le=50)
    required: bool | None = None


class AttachGroupRequest(CamelModel):
    modifier_group_id: UUID


class PriceLineRequest(CamelModel):
    product_id: UUID
    option_ids: list[UUID] = Field(default_factory=list)


class PriceLineResponse(CamelModel):
    product_id: UUID
    base_price_cents: int
    modifier_delta_cents: int
    total_cents: int
