from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.modules.discounts.entity import DiscountKind


class DiscountRead(CamelModel):
    id: UUID
    code: str
    name: str
    kind: DiscountKind
    percent: Decimal | None
    amount_cents: int | None
    currency: str
    is_active: bool
    starts_at: datetime | None
    ends_at: datetime | None


class DiscountCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    kind: DiscountKind
    percent: Decimal | None = None
    amount_cents: int | None = None
    currency: str = "BDT"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
