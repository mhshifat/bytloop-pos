from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from src.core.schemas import CamelModel
from src.modules.procurement.entity import PurchaseOrderStatus


class SupplierRead(CamelModel):
    id: UUID
    code: str
    name: str
    email: EmailStr | None
    phone: str | None


class SupplierCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


class PurchaseOrderItemInput(CamelModel):
    product_id: UUID
    quantity_ordered: int = Field(ge=1)
    unit_cost_cents: int = Field(ge=0)


class PurchaseOrderCreate(CamelModel):
    supplier_id: UUID
    items: list[PurchaseOrderItemInput] = Field(min_length=1)
    currency: str = "BDT"


class PurchaseOrderItemRead(CamelModel):
    id: UUID
    product_id: UUID
    quantity_ordered: int
    quantity_received: int
    unit_cost_cents: int
    line_total_cents: int


class PurchaseOrderRead(CamelModel):
    id: UUID
    supplier_id: UUID
    number: str
    status: PurchaseOrderStatus
    total_cents: int
    currency: str
    created_at: datetime
    sent_at: datetime | None
    closed_at: datetime | None
    items: list[PurchaseOrderItemRead] = []


class PurchaseOrderSummary(CamelModel):
    id: UUID
    supplier_id: UUID
    number: str
    status: PurchaseOrderStatus
    total_cents: int
    currency: str
    created_at: datetime


class PurchaseOrderList(CamelModel):
    items: list[PurchaseOrderSummary]
    has_more: bool
    page: int
    page_size: int


class ReceiveItemInput(CamelModel):
    item_id: UUID
    quantity: int = Field(ge=1)


class ReceiveRequest(CamelModel):
    items: list[ReceiveItemInput] = Field(min_length=1)
