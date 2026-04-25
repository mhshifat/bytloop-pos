"""Cafeteria — employee / student meal-plan subscriptions.

A ``MealPlan`` defines a template (e.g. "20 meals / 30 days / 15000c").
A ``MealPlanSubscription`` is the per-customer instance with remaining
meal count. A ``MealRedemption`` is the audit log written each time a
meal is consumed at the POS.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class MealPlan(Base):
    __tablename__ = "meal_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_meal_plans_tenant_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    meals_per_period: Mapped[int] = mapped_column()
    period_days: Mapped[int] = mapped_column(default=30)
    price_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class MealPlanSubscription(Base):
    __tablename__ = "meal_plan_subscriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    # Denormalised code (not FK): plans can be renamed or deleted without
    # invalidating historical subscriptions.
    plan_code: Mapped[str] = mapped_column(String(32))
    meals_remaining: Mapped[int] = mapped_column()
    period_ends_on: Mapped[date] = mapped_column(Date())
    auto_renew: Mapped[bool] = mapped_column(default=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(16), default=SubscriptionStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class MealRedemption(Base):
    __tablename__ = "meal_redemptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    subscription_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("meal_plan_subscriptions.id", ondelete="CASCADE"),
        index=True,
    )
    # SET NULL — purging ancient orders should preserve the redemption
    # audit history (we still know a meal was consumed, just not which order).
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    meals_used: Mapped[int] = mapped_column(default=1)
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
