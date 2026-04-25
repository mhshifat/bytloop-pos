from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.logistics.deliveries.schemas import (
    DeliveryScheduleRead,
    MarkFailedRequest,
    ScheduleRequest,
)
from src.verticals.logistics.deliveries.service import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.post(
    "",
    response_model=DeliveryScheduleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def schedule_delivery(
    data: ScheduleRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DeliveryScheduleRead:
    schedule = await DeliveryService(db).schedule(tenant_id=user.tenant_id, data=data)
    return DeliveryScheduleRead.model_validate(schedule)


@router.get(
    "/scheduled",
    response_model=list[DeliveryScheduleRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_scheduled(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    day: date = Query(...),
) -> list[DeliveryScheduleRead]:
    rows = await DeliveryService(db).list_scheduled(
        tenant_id=user.tenant_id, day=day
    )
    return [DeliveryScheduleRead.model_validate(r) for r in rows]


@router.get(
    "/by-order/{order_id}",
    response_model=list[DeliveryScheduleRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_for_order(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[DeliveryScheduleRead]:
    rows = await DeliveryService(db).list_for_order(
        tenant_id=user.tenant_id, order_id=order_id
    )
    return [DeliveryScheduleRead.model_validate(r) for r in rows]


@router.get(
    "/{delivery_id}",
    response_model=DeliveryScheduleRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_delivery(
    delivery_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DeliveryScheduleRead:
    schedule = await DeliveryService(db).get(
        tenant_id=user.tenant_id, delivery_id=delivery_id
    )
    return DeliveryScheduleRead.model_validate(schedule)


@router.post(
    "/{delivery_id}/out-for-delivery",
    response_model=DeliveryScheduleRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_out_for_delivery(
    delivery_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DeliveryScheduleRead:
    schedule = await DeliveryService(db).mark_out_for_delivery(
        tenant_id=user.tenant_id, delivery_id=delivery_id
    )
    return DeliveryScheduleRead.model_validate(schedule)


@router.post(
    "/{delivery_id}/delivered",
    response_model=DeliveryScheduleRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_delivered(
    delivery_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DeliveryScheduleRead:
    schedule = await DeliveryService(db).mark_delivered(
        tenant_id=user.tenant_id, delivery_id=delivery_id
    )
    return DeliveryScheduleRead.model_validate(schedule)


@router.post(
    "/{delivery_id}/failed",
    response_model=DeliveryScheduleRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_failed(
    delivery_id: UUID,
    data: MarkFailedRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DeliveryScheduleRead:
    schedule = await DeliveryService(db).mark_failed(
        tenant_id=user.tenant_id, delivery_id=delivery_id, reason=data.reason
    )
    return DeliveryScheduleRead.model_validate(schedule)
