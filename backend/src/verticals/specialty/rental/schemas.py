from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.specialty.rental.entity import RentalStatus


class AssetRead(CamelModel):
    id: UUID
    code: str
    label: str
    hourly_rate_cents: int
    daily_rate_cents: int


class AssetCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    label: str = Field(min_length=1, max_length=128)
    hourly_rate_cents: int = Field(ge=0)
    daily_rate_cents: int = Field(ge=0)


class ContractRead(CamelModel):
    id: UUID
    asset_id: UUID
    customer_id: UUID
    status: RentalStatus
    starts_at: datetime
    ends_at: datetime
    returned_at: datetime | None
    deposit_cents: int
    late_fee_cents: int = 0
    damage_fee_cents: int = 0
    damage_notes: str | None = None


class ContractCreate(CamelModel):
    asset_id: UUID
    customer_id: UUID
    starts_at: datetime
    ends_at: datetime
    deposit_cents: int = Field(default=0, ge=0)


class ReturnRequest(CamelModel):
    returned_at: datetime | None = None
    damage_fee_cents: int = Field(default=0, ge=0)
    damage_notes: str | None = Field(default=None, max_length=2048)


class ReturnSummaryRead(CamelModel):
    contract: ContractRead
    base_rental_cents: int
    late_fee_cents: int
    damage_fee_cents: int
    deposit_refund_cents: int
    net_due_cents: int
