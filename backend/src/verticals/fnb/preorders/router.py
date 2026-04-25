from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.preorders.schemas import (
    ConvertToOrderRequest,
    PreorderCreate,
    PreorderItemRead,
    PreorderRead,
    UpdatePreorderStatusRequest,
)
from src.verticals.fnb.preorders.service import PreorderService

router = APIRouter(prefix="/preorders", tags=["preorders"])


async def _to_read(svc: PreorderService, *, tenant_id: UUID, preorder) -> PreorderRead:  # type: ignore[no-untyped-def]
    items = await svc.list_items(tenant_id=tenant_id, preorder_id=preorder.id)
    return PreorderRead(
        id=preorder.id,
        customer_id=preorder.customer_id,
        pickup_at=preorder.pickup_at,
        status=preorder.status,
        order_id=preorder.order_id,
        notes=preorder.notes,
        total_cents=preorder.total_cents,
        items=[PreorderItemRead.model_validate(i) for i in items],
    )


@router.post(
    "",
    response_model=PreorderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_preorder(
    data: PreorderCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PreorderRead:
    svc = PreorderService(db)
    preorder = await svc.create(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        pickup_at=data.pickup_at,
        notes=data.notes,
        items=data.items,
    )
    return await _to_read(svc, tenant_id=user.tenant_id, preorder=preorder)


@router.get(
    "",
    response_model=list[PreorderRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_upcoming(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=7, ge=1, le=90),
) -> list[PreorderRead]:
    svc = PreorderService(db)
    rows = await svc.list_upcoming(tenant_id=user.tenant_id, days=days)
    return [await _to_read(svc, tenant_id=user.tenant_id, preorder=r) for r in rows]


@router.get(
    "/by-day",
    response_model=list[PreorderRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_for_day(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    day: date = Query(...),
) -> list[PreorderRead]:
    svc = PreorderService(db)
    rows = await svc.list_for_day(tenant_id=user.tenant_id, day=day)
    return [await _to_read(svc, tenant_id=user.tenant_id, preorder=r) for r in rows]


@router.get(
    "/{preorder_id}",
    response_model=PreorderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_preorder(
    preorder_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PreorderRead:
    svc = PreorderService(db)
    preorder = await svc.get(tenant_id=user.tenant_id, preorder_id=preorder_id)
    return await _to_read(svc, tenant_id=user.tenant_id, preorder=preorder)


@router.patch(
    "/{preorder_id}/status",
    response_model=PreorderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_status(
    preorder_id: UUID,
    data: UpdatePreorderStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PreorderRead:
    svc = PreorderService(db)
    preorder = await svc.update_status(
        tenant_id=user.tenant_id, preorder_id=preorder_id, status=data.status
    )
    return await _to_read(svc, tenant_id=user.tenant_id, preorder=preorder)


@router.post(
    "/{preorder_id}/convert",
    response_model=PreorderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def convert_to_order(
    preorder_id: UUID,
    data: ConvertToOrderRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PreorderRead:
    svc = PreorderService(db)
    preorder = await svc.convert_to_order(
        tenant_id=user.tenant_id,
        cashier_id=user.id,
        preorder_id=preorder_id,
        payment_method=data.payment_method,
        amount_tendered_cents=data.amount_tendered_cents,
        payment_reference=data.payment_reference,
    )
    return await _to_read(svc, tenant_id=user.tenant_id, preorder=preorder)
