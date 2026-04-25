from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.fnb.cafeteria.entity import (
    MealPlan,
    MealPlanSubscription,
    MealRedemption,
    SubscriptionStatus,
)


class CafeteriaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Plans
    # ──────────────────────────────────────────────

    async def create_plan(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        meals_per_period: int,
        period_days: int = 30,
        price_cents: int = 0,
    ) -> MealPlan:
        stmt = select(MealPlan).where(
            MealPlan.tenant_id == tenant_id, MealPlan.code == code
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("A meal plan with this code already exists.")
        plan = MealPlan(
            tenant_id=tenant_id,
            code=code,
            name=name,
            meals_per_period=meals_per_period,
            period_days=period_days,
            price_cents=price_cents,
        )
        self._session.add(plan)
        await self._session.flush()
        return plan

    async def list_plans(self, *, tenant_id: UUID) -> list[MealPlan]:
        stmt = (
            select(MealPlan)
            .where(MealPlan.tenant_id == tenant_id)
            .order_by(MealPlan.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_plan_by_code(
        self, *, tenant_id: UUID, plan_code: str
    ) -> MealPlan:
        stmt = select(MealPlan).where(
            MealPlan.tenant_id == tenant_id, MealPlan.code == plan_code
        )
        plan = (await self._session.execute(stmt)).scalar_one_or_none()
        if plan is None:
            raise NotFoundError("Meal plan not found.")
        return plan

    # ──────────────────────────────────────────────
    # Subscriptions
    # ──────────────────────────────────────────────

    async def subscribe(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        plan_code: str,
        starts_on: date,
        auto_renew: bool = False,
    ) -> MealPlanSubscription:
        plan = await self._get_plan_by_code(tenant_id=tenant_id, plan_code=plan_code)
        sub = MealPlanSubscription(
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_code=plan.code,
            meals_remaining=plan.meals_per_period,
            period_ends_on=starts_on + timedelta(days=plan.period_days),
            auto_renew=auto_renew,
            status=SubscriptionStatus.ACTIVE,
        )
        self._session.add(sub)
        await self._session.flush()
        return sub

    async def get_subscription(
        self, *, tenant_id: UUID, subscription_id: UUID
    ) -> MealPlanSubscription:
        sub = await self._session.get(MealPlanSubscription, subscription_id)
        if sub is None or sub.tenant_id != tenant_id:
            raise NotFoundError("Subscription not found.")
        return sub

    async def list_subscriptions(
        self, *, tenant_id: UUID, customer_id: UUID | None = None
    ) -> list[MealPlanSubscription]:
        stmt = select(MealPlanSubscription).where(
            MealPlanSubscription.tenant_id == tenant_id
        )
        if customer_id is not None:
            stmt = stmt.where(MealPlanSubscription.customer_id == customer_id)
        stmt = stmt.order_by(MealPlanSubscription.created_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def pause(
        self, *, tenant_id: UUID, subscription_id: UUID
    ) -> MealPlanSubscription:
        sub = await self.get_subscription(
            tenant_id=tenant_id, subscription_id=subscription_id
        )
        if sub.status != SubscriptionStatus.ACTIVE:
            raise ConflictError("Only active subscriptions can be paused.")
        sub.status = SubscriptionStatus.PAUSED
        await self._session.flush()
        return sub

    async def resume(
        self, *, tenant_id: UUID, subscription_id: UUID
    ) -> MealPlanSubscription:
        sub = await self.get_subscription(
            tenant_id=tenant_id, subscription_id=subscription_id
        )
        if sub.status != SubscriptionStatus.PAUSED:
            raise ConflictError("Only paused subscriptions can be resumed.")
        sub.status = SubscriptionStatus.ACTIVE
        await self._session.flush()
        return sub

    # ──────────────────────────────────────────────
    # Redemption
    # ──────────────────────────────────────────────

    async def redeem(
        self,
        *,
        tenant_id: UUID,
        subscription_id: UUID,
        meals_used: int = 1,
        order_id: UUID | None = None,
    ) -> MealRedemption:
        """Decrement meals_remaining and log the redemption.

        Raises ConflictError if the subscription isn't active, is already
        past its period, or has insufficient meals remaining. Any leftover
        meals at renewal do NOT roll over — see ``renew``.
        """
        sub = await self.get_subscription(
            tenant_id=tenant_id, subscription_id=subscription_id
        )
        if sub.status != SubscriptionStatus.ACTIVE:
            raise ConflictError("Subscription is not active.")
        today = datetime.now(tz=UTC).date()
        if sub.period_ends_on < today:
            sub.status = SubscriptionStatus.EXPIRED
            await self._session.flush()
            raise ConflictError("Subscription period has ended.")
        if sub.meals_remaining < meals_used:
            raise ConflictError("Insufficient meals remaining on this subscription.")

        sub.meals_remaining -= meals_used
        redemption = MealRedemption(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            order_id=order_id,
            meals_used=meals_used,
        )
        self._session.add(redemption)
        await self._session.flush()
        return redemption

    async def list_redemptions(
        self, *, tenant_id: UUID, subscription_id: UUID
    ) -> list[MealRedemption]:
        await self.get_subscription(
            tenant_id=tenant_id, subscription_id=subscription_id
        )
        stmt = (
            select(MealRedemption)
            .where(
                MealRedemption.tenant_id == tenant_id,
                MealRedemption.subscription_id == subscription_id,
            )
            .order_by(MealRedemption.redeemed_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def renew(
        self, *, tenant_id: UUID, subscription_id: UUID
    ) -> MealPlanSubscription:
        """Reset meals and push period_ends_on forward by plan.period_days.

        Any unused meals from the current period are FORFEITED — subscription
        meal plans intentionally do not accumulate.
        """
        sub = await self.get_subscription(
            tenant_id=tenant_id, subscription_id=subscription_id
        )
        plan = await self._get_plan_by_code(
            tenant_id=tenant_id, plan_code=sub.plan_code
        )
        today = datetime.now(tz=UTC).date()
        # New period starts the later of (today, current period end) so
        # early renewals don't shorten the window.
        base = sub.period_ends_on if sub.period_ends_on > today else today
        sub.meals_remaining = plan.meals_per_period
        sub.period_ends_on = base + timedelta(days=plan.period_days)
        sub.status = SubscriptionStatus.ACTIVE
        await self._session.flush()
        return sub
