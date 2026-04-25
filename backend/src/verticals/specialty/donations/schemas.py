from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class CampaignCreate(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    goal_cents: int = Field(ge=0, default=0)
    starts_on: date | None = None
    ends_on: date | None = None
    active: bool = True


class CampaignRead(CamelModel):
    id: UUID
    code: str
    name: str
    goal_cents: int
    starts_on: date | None = None
    ends_on: date | None = None
    active: bool


class DonationCreate(CamelModel):
    customer_id: UUID | None = None
    amount_cents: int = Field(gt=0)
    currency: str = Field(default="BDT", min_length=3, max_length=3)
    campaign: str | None = Field(default=None, max_length=64)
    donor_name_override: str | None = Field(default=None, max_length=255)
    is_anonymous: bool = False
    tax_deductible: bool = True


class DonationRead(CamelModel):
    id: UUID
    customer_id: UUID | None = None
    amount_cents: int
    currency: str
    campaign: str | None = None
    donor_name_override: str | None = None
    is_anonymous: bool
    tax_deductible: bool
    receipt_no: str
    received_at: datetime


class CampaignTotals(CamelModel):
    code: str
    donation_count: int
    total_cents: int
    goal_cents: int
    progress_pct: float


class DonationReceipt(CamelModel):
    receipt_no: str
    donor_name: str
    amount_cents: int
    currency: str
    campaign: str | None = None
    tax_deductible: bool
    received_at: datetime
