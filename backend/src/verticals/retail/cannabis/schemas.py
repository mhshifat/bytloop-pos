from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.retail.cannabis.entity import (
    BatchState,
    MetrcSyncStatus,
    TransactionKind,
)


class BatchRead(CamelModel):
    id: UUID
    batch_id: str
    product_id: UUID
    strain_name: str
    thc_pct: Decimal
    cbd_pct: Decimal
    harvested_on: date
    expires_on: date
    quantity_grams: Decimal
    state: BatchState


class BatchCreate(CamelModel):
    batch_id: str = Field(min_length=1, max_length=64)
    product_id: UUID
    strain_name: str = Field(min_length=1, max_length=128)
    thc_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    cbd_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    harvested_on: date
    expires_on: date
    quantity_grams: Decimal = Field(gt=0)


class TransactionRead(CamelModel):
    id: UUID
    batch_id: UUID
    kind: TransactionKind
    grams_delta: Decimal
    order_id: UUID | None
    customer_id: UUID | None
    reason: str | None
    recorded_by_user_id: UUID | None
    recorded_at: datetime
    metrc_sync_status: MetrcSyncStatus
    metrc_sync_error: str | None


class SellRequest(CamelModel):
    batch_id: UUID
    customer_id: UUID
    grams: Decimal = Field(gt=0)
    order_id: UUID | None = None


class DestroyRequest(CamelModel):
    batch_id: UUID
    grams: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=512)


class RecallRequest(CamelModel):
    batch_id: UUID
    reason: str = Field(min_length=1, max_length=512)


class MarkSyncFailedRequest(CamelModel):
    error: str = Field(min_length=1, max_length=1024)
