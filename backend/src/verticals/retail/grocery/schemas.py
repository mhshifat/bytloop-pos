from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class PluLookupResponse(CamelModel):
    product_id: UUID


class WeightPriceRequest(CamelModel):
    product_id: UUID
    grams: int = Field(ge=0)


class WeightPriceResponse(CamelModel):
    price_cents: int


class PluCreate(CamelModel):
    code: str = Field(min_length=3, max_length=8)
    product_id: UUID


class PluRead(CamelModel):
    id: UUID
    code: str
    product_id: UUID


class WeighableUpsert(CamelModel):
    product_id: UUID
    sell_unit: str = Field(default="kg")
    price_per_unit_cents: int = Field(ge=0)
    tare_grams: int = Field(default=0, ge=0)


class WeighableRead(CamelModel):
    product_id: UUID
    sell_unit: str
    price_per_unit_cents: int
    tare_grams: int


class ScanRequest(CamelModel):
    input_code: str = Field(min_length=1, max_length=32)


class ScanResponse(CamelModel):
    product_id: UUID
    line_total_cents: int | None = None
