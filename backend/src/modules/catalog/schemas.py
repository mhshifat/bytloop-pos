from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class ProductRead(CamelModel):
    id: UUID
    sku: str
    barcode: str | None
    name: str
    description: str | None
    category_id: UUID | None
    price_cents: int
    currency: str
    is_active: bool
    track_inventory: bool
    tax_rate: Decimal
    vertical_data: dict[str, Any] = Field(default_factory=dict)


class ProductCreate(CamelModel):
    sku: str = Field(min_length=1, max_length=64)
    barcode: str | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    price_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    is_active: bool = True
    track_inventory: bool = True
    tax_rate: Decimal = Decimal("0")
    vertical_data: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(CamelModel):
    name: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = None
    is_active: bool | None = None
    track_inventory: bool | None = None
    tax_rate: Decimal | None = None
    vertical_data: dict[str, Any] | None = None


class ProductList(CamelModel):
    items: list[ProductRead]
    has_more: bool
    page: int
    page_size: int


class CategoryRead(CamelModel):
    id: UUID
    slug: str
    name: str
    parent_id: UUID | None


class CategoryCreate(CamelModel):
    slug: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    parent_id: UUID | None = None
