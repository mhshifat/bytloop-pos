from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class LoyaltyCardRead(CamelModel):
    id: UUID
    customer_id: UUID
    card_code: str
    punches_current: int
    punches_required: int
    free_items_earned: int
    total_punches_lifetime: int


class IssueCardRequest(CamelModel):
    customer_id: UUID
    card_code: str = Field(min_length=1, max_length=64)
    punches_required: int = Field(default=10, ge=1, le=100)


class PunchRequest(CamelModel):
    card_code: str = Field(min_length=1, max_length=64)
    count: int = Field(default=1, ge=1, le=100)


class PunchResponse(CamelModel):
    card: LoyaltyCardRead
    # True when this call pushed the card across a ``punches_required``
    # boundary at least once — UI can use it to trigger a celebratory toast.
    earned_this_punch: bool


class RedeemRequest(CamelModel):
    card_code: str = Field(min_length=1, max_length=64)
