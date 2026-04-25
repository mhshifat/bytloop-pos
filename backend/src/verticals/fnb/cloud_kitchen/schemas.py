from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class CreateBrandRequest(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    logo_url: str | None = Field(default=None, max_length=512)
    is_active: bool = True


class UpdateBrandRequest(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    logo_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


class VirtualBrandRead(CamelModel):
    id: UUID
    code: str
    name: str
    logo_url: str | None
    is_active: bool
    created_at: datetime


class AttachProductRequest(CamelModel):
    product_id: UUID


class BrandProductRead(CamelModel):
    brand_id: UUID
    product_id: UUID
    created_at: datetime


class RecordBrandOrderRequest(CamelModel):
    order_id: UUID
    brand_id: UUID
    external_order_ref: str | None = Field(default=None, max_length=128)


class BrandOrderRead(CamelModel):
    id: UUID
    order_id: UUID
    brand_id: UUID
    external_order_ref: str | None
    created_at: datetime
