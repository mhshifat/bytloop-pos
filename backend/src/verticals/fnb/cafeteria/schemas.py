from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.fnb.cafeteria.entity import SubscriptionStatus


class CreatePlanRequest(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    meals_per_period: int = Field(ge=1)
    period_days: int = Field(default=30, ge=1, le=366)
    price_cents: int = Field(default=0, ge=0)


class MealPlanRead(CamelModel):
    id: UUID
    code: str
    name: str
    meals_per_period: int
    period_days: int
    price_cents: int
    created_at: datetime


class SubscribeRequest(CamelModel):
    customer_id: UUID
    plan_code: str = Field(min_length=1, max_length=32)
    starts_on: date
    auto_renew: bool = False


class SubscriptionRead(CamelModel):
    id: UUID
    customer_id: UUID
    plan_code: str
    meals_remaining: int
    period_ends_on: date
    auto_renew: bool
    status: SubscriptionStatus
    created_at: datetime


class RedeemRequest(CamelModel):
    meals_used: int = Field(default=1, ge=1)
    order_id: UUID | None = None


class RedemptionRead(CamelModel):
    id: UUID
    subscription_id: UUID
    order_id: UUID | None
    meals_used: int
    redeemed_at: datetime
