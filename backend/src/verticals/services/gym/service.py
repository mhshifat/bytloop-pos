from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, ForbiddenError, NotFoundError
from src.verticals.services.gym.entity import (
    CheckIn,
    GymClass,
    GymClassBooking,
    GymPlan,
    Membership,
    MembershipStatus,
)


class GymService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Plan catalog
    # ──────────────────────────────────────────────

    async def list_plans(self, *, tenant_id: UUID) -> list[GymPlan]:
        stmt = (
            select(GymPlan)
            .where(GymPlan.tenant_id == tenant_id)
            .order_by(GymPlan.duration_days)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def upsert_plan(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        duration_days: int,
        price_cents: int,
        is_active: bool = True,
    ) -> GymPlan:
        stmt = select(GymPlan).where(
            GymPlan.tenant_id == tenant_id, GymPlan.code == code
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.name = name
            existing.duration_days = duration_days
            existing.price_cents = price_cents
            existing.is_active = is_active
            await self._session.flush()
            return existing
        plan = GymPlan(
            tenant_id=tenant_id,
            code=code,
            name=name,
            duration_days=duration_days,
            price_cents=price_cents,
            is_active=is_active,
        )
        self._session.add(plan)
        await self._session.flush()
        return plan

    # ──────────────────────────────────────────────
    # Memberships
    # ──────────────────────────────────────────────

    async def list_memberships(self, *, tenant_id: UUID) -> list[Membership]:
        stmt = (
            select(Membership)
            .where(Membership.tenant_id == tenant_id)
            .order_by(Membership.ends_on)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_membership(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        plan_code: str,
        starts_on: date,
        ends_on: date,
    ) -> Membership:
        membership = Membership(
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_code=plan_code,
            status=MembershipStatus.ACTIVE,
            starts_on=starts_on,
            ends_on=ends_on,
        )
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def create_membership_from_plan(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        plan_code: str,
        starts_on: date | None = None,
    ) -> Membership:
        """Resolve the plan's duration and create the membership in one shot."""
        stmt = select(GymPlan).where(
            GymPlan.tenant_id == tenant_id,
            GymPlan.code == plan_code,
            GymPlan.is_active.is_(True),
        )
        plan = (await self._session.execute(stmt)).scalar_one_or_none()
        if plan is None:
            raise NotFoundError(f"Plan {plan_code} not found or inactive.")
        start = starts_on or date.today()
        return await self.create_membership(
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_code=plan.code,
            starts_on=start,
            ends_on=start + timedelta(days=plan.duration_days),
        )

    # ──────────────────────────────────────────────
    # Check-in gate
    # ──────────────────────────────────────────────

    async def check_in(self, *, tenant_id: UUID, membership_id: UUID) -> CheckIn:
        """Refuse if the membership isn't active, or if today is past its end."""
        membership = await self._session.get(Membership, membership_id)
        if membership is None or membership.tenant_id != tenant_id:
            raise NotFoundError("Membership not found.")
        if membership.status != MembershipStatus.ACTIVE:
            raise ForbiddenError(
                f"Membership is {membership.status.value} — access denied.",
                code="membership_inactive",
            )
        today = date.today()
        if today > membership.ends_on:
            # Auto-roll to EXPIRED so the next check-in gets a clearer error.
            membership.status = MembershipStatus.EXPIRED
            await self._session.flush()
            raise ForbiddenError(
                "Membership expired. Renew before checking in.",
                code="membership_expired",
            )
        event = CheckIn(tenant_id=tenant_id, membership_id=membership_id)
        self._session.add(event)
        await self._session.flush()
        return event

    # ──────────────────────────────────────────────
    # Classes + bookings
    # ──────────────────────────────────────────────

    async def list_classes(
        self, *, tenant_id: UUID, after: datetime | None = None
    ) -> list[GymClass]:
        since = after or datetime.utcnow()
        stmt = (
            select(GymClass)
            .where(
                GymClass.tenant_id == tenant_id,
                GymClass.starts_at >= since,
            )
            .order_by(GymClass.starts_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def schedule_class(
        self,
        *,
        tenant_id: UUID,
        title: str,
        trainer_id: UUID | None,
        starts_at: datetime,
        ends_at: datetime,
        capacity: int,
    ) -> GymClass:
        gym_class = GymClass(
            tenant_id=tenant_id,
            title=title,
            trainer_id=trainer_id,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity,
        )
        self._session.add(gym_class)
        await self._session.flush()
        return gym_class

    async def book_class(
        self, *, tenant_id: UUID, class_id: UUID, membership_id: UUID
    ) -> GymClassBooking:
        """Capacity-gated booking. Refuses duplicates (unique constraint)
        and full classes. Membership must be ACTIVE.
        """
        gym_class = await self._session.get(GymClass, class_id)
        if gym_class is None or gym_class.tenant_id != tenant_id:
            raise NotFoundError("Class not found.")
        membership = await self._session.get(Membership, membership_id)
        if membership is None or membership.tenant_id != tenant_id:
            raise NotFoundError("Membership not found.")
        if membership.status != MembershipStatus.ACTIVE:
            raise ForbiddenError("Only active members can book classes.")

        count_stmt = select(func.count(GymClassBooking.id)).where(
            GymClassBooking.class_id == class_id
        )
        current = (await self._session.execute(count_stmt)).scalar_one()
        if int(current or 0) >= gym_class.capacity:
            raise ConflictError("Class is full.")

        booking = GymClassBooking(
            tenant_id=tenant_id, class_id=class_id, membership_id=membership_id
        )
        self._session.add(booking)
        await self._session.flush()
        return booking
