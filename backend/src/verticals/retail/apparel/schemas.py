from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class ApparelVariantRead(CamelModel):
    id: UUID
    product_id: UUID
    sku: str
    barcode: str | None
    size: str
    color: str
    gender: str | None = None
    fit: str | None = None
    material: str | None = None
    price_cents_override: int | None
    stock_quantity: int = 0


class GenerateMatrixRequest(CamelModel):
    product_id: UUID
    sizes: list[str] = Field(min_length=1)
    colors: list[str] = Field(min_length=1)
    sku_prefix: str = Field(min_length=1, max_length=16)


class VariantUpdateRequest(CamelModel):
    barcode: str | None = None
    gender: str | None = Field(default=None, max_length=8)
    fit: str | None = Field(default=None, max_length=32)
    material: str | None = Field(default=None, max_length=64)
    price_cents_override: int | None = None


class VariantStockAdjust(CamelModel):
    delta: int
