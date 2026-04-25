from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.cafeteria.schemas import (
    CreatePlanRequest,
    MealPlanRead,
    RedeemRequest,
    RedemptionRead,
    SubscribeRequest,
    SubscriptionRead,
)
from src.verticals.fnb.cafeteria.service import CafeteriaService

router = APIRouter(prefix="/cafeteria", tags=["cafeteria"])


@router.post(
    "/plans",
    response_model=MealPlanRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_plan(
    data: CreatePlanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> MealPlanRead:
    plan = await CafeteriaService(db).create_plan(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        meals_per_period=data.meals_per_period,
        period_days=data.period_days,
        price_cents=data.price_cents,
    )
    return MealPlanRead.model_validate(plan)


@router.get(
    "/plans",
    response_model=list[MealPlanRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_plans(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[MealPlanRead]:
    plans = await CafeteriaService(db).list_plans(tenant_id=user.tenant_id)
    return [MealPlanRead.model_validate(p) for p in plans]


@router.post(
    "/subscriptions",
    response_model=SubscriptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def subscribe(
    data: SubscribeRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SubscriptionRead:
    sub = await CafeteriaService(db).subscribe(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        plan_code=data.plan_code,
        starts_on=data.starts_on,
        auto_renew=data.auto_renew,
    )
    return SubscriptionRead.model_validate(sub)


@router.get(
    "/subscriptions",
    response_model=list[SubscriptionRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_subscriptions(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    customer_id: UUID | None = Query(default=None),
) -> list[SubscriptionRead]:
    subs = await CafeteriaService(db).list_subscriptions(
        tenant_id=user.tenant_id, customer_id=customer_id
    )
    return [SubscriptionRead.model_validate(s) for s in subs]


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_subscription(
    subscription_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SubscriptionRead:
    sub = await CafeteriaService(db).get_subscription(
        tenant_id=user.tenant_id, subscription_id=subscription_id
    )
    return SubscriptionRead.model_validate(sub)


@router.post(
    "/subscriptions/{subscription_id}/pause",
    response_model=SubscriptionRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def pause_subscription(
    subscription_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SubscriptionRead:
    sub = await CafeteriaService(db).pause(
        tenant_id=user.tenant_id, subscription_id=subscription_id
    )
    return SubscriptionRead.model_validate(sub)


@router.post(
    "/subscriptions/{subscription_id}/resume",
    response_model=SubscriptionRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def resume_subscription(
    subscription_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SubscriptionRead:
    sub = await CafeteriaService(db).resume(
        tenant_id=user.tenant_id, subscription_id=subscription_id
    )
    return SubscriptionRead.model_validate(sub)


@router.post(
    "/subscriptions/{subscription_id}/redeem",
    response_model=RedemptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def redeem(
    subscription_id: UUID,
    data: RedeemRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RedemptionRead:
    redemption = await CafeteriaService(db).redeem(
        tenant_id=user.tenant_id,
        subscription_id=subscription_id,
        meals_used=data.meals_used,
        order_id=data.order_id,
    )
    return RedemptionRead.model_validate(redemption)


@router.get(
    "/subscriptions/{subscription_id}/redemptions",
    response_model=list[RedemptionRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_redemptions(
    subscription_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[RedemptionRead]:
    rows = await CafeteriaService(db).list_redemptions(
        tenant_id=user.tenant_id, subscription_id=subscription_id
    )
    return [RedemptionRead.model_validate(r) for r in rows]


@router.post(
    "/subscriptions/{subscription_id}/renew",
    response_model=SubscriptionRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def renew_subscription(
    subscription_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SubscriptionRead:
    sub = await CafeteriaService(db).renew(
        tenant_id=user.tenant_id, subscription_id=subscription_id
    )
    return SubscriptionRead.model_validate(sub)
