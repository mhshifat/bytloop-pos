from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.gym.schemas import (
    CheckInRead,
    CheckInRequest,
    ClassBookingRead,
    ClassBookingRequest,
    ClassCreate,
    ClassRead,
    MembershipCreate,
    MembershipFromPlan,
    MembershipRead,
    PlanRead,
    PlanUpsert,
)
from src.verticals.services.gym.service import GymService

router = APIRouter(prefix="/gym", tags=["gym"])


@router.get(
    "/plans",
    response_model=list[PlanRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_plans(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PlanRead]:
    rows = await GymService(db).list_plans(tenant_id=user.tenant_id)
    return [PlanRead.model_validate(r) for r in rows]


@router.put(
    "/plans",
    response_model=PlanRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_plan(
    data: PlanUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PlanRead:
    plan = await GymService(db).upsert_plan(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        duration_days=data.duration_days,
        price_cents=data.price_cents,
        is_active=data.is_active,
    )
    return PlanRead.model_validate(plan)


@router.get(
    "/memberships",
    response_model=list[MembershipRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_memberships(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[MembershipRead]:
    rows = await GymService(db).list_memberships(tenant_id=user.tenant_id)
    return [MembershipRead.model_validate(r) for r in rows]


@router.post(
    "/memberships",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_membership(
    data: MembershipCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> MembershipRead:
    membership = await GymService(db).create_membership(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        plan_code=data.plan_code,
        starts_on=data.starts_on,
        ends_on=data.ends_on,
    )
    return MembershipRead.model_validate(membership)


@router.post(
    "/memberships/from-plan",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_membership_from_plan(
    data: MembershipFromPlan,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> MembershipRead:
    membership = await GymService(db).create_membership_from_plan(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        plan_code=data.plan_code,
        starts_on=data.starts_on,
    )
    return MembershipRead.model_validate(membership)


@router.post(
    "/checkins",
    response_model=CheckInRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def check_in(
    data: CheckInRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CheckInRead:
    event = await GymService(db).check_in(
        tenant_id=user.tenant_id, membership_id=data.membership_id
    )
    return CheckInRead.model_validate(event)


@router.get(
    "/classes",
    response_model=list[ClassRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_classes(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ClassRead]:
    rows = await GymService(db).list_classes(tenant_id=user.tenant_id)
    return [ClassRead.model_validate(r) for r in rows]


@router.post(
    "/classes",
    response_model=ClassRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def schedule_class(
    data: ClassCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ClassRead:
    gym_class = await GymService(db).schedule_class(
        tenant_id=user.tenant_id,
        title=data.title,
        trainer_id=data.trainer_id,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        capacity=data.capacity,
    )
    return ClassRead.model_validate(gym_class)


@router.post(
    "/classes/{class_id}/bookings",
    response_model=ClassBookingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def book_class(
    class_id: UUID,
    data: ClassBookingRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ClassBookingRead:
    booking = await GymService(db).book_class(
        tenant_id=user.tenant_id,
        class_id=class_id,
        membership_id=data.membership_id,
    )
    return ClassBookingRead.model_validate(booking)
