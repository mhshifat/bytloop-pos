from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.fnb.bar_tabs.entity import BarTabStatus


class OpenTabRequest(CamelModel):
    customer_id: UUID | None = None
    preauth_reference: str | None = Field(default=None, max_length=128)


class AddLineRequest(CamelModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1)
    unit_price_cents: int = Field(ge=0)


class BarTabLineRead(CamelModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price_cents: int
    added_at: datetime


class BarTabRead(CamelModel):
    id: UUID
    customer_id: UUID | None
    status: BarTabStatus
    preauth_reference: str | None
    opened_at: datetime
    closed_at: datetime | None
    order_id: UUID | None
    total_cents: int
    lines: list[BarTabLineRead] = []


class CloseTabRequest(CamelModel):
    """Close payload is intentionally empty today — the tab settles against
    its own pre-auth reference via the sales checkout. Reserved for future
    tip overrides.
    """
