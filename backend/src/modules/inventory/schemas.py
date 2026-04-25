from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class InventoryLevelRead(CamelModel):
    id: UUID
    product_id: UUID
    product_name: str
    sku: str
    location_id: UUID
    location_code: str
    location_name: str
    quantity: int
    reorder_point: int
    updated_at: datetime


class InventoryLevelList(CamelModel):
    items: list[InventoryLevelRead]
    has_more: bool
    page: int
    page_size: int


class LocationRead(CamelModel):
    id: UUID
    code: str
    name: str


class LocationCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)


class StockAdjustRequest(CamelModel):
    product_id: UUID
    delta: int = Field(description="Positive = receive, negative = adjust out")
    reason: str = Field(default="adjustment", max_length=32)


class ReorderPointRequest(CamelModel):
    product_id: UUID
    reorder_point: int = Field(ge=0)


class TransferRequest(CamelModel):
    product_id: UUID
    source_location_id: UUID
    destination_location_id: UUID
    quantity: int = Field(gt=0)


class TransferResult(CamelModel):
    source_quantity: int
    destination_quantity: int
