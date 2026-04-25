from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.furniture.entity import CustomOrderStatus
from src.verticals.retail.furniture.schemas import (
    CancelRequest,
    CustomOrderRead,
    MarkDeliveredRequest,
    QuoteRequest,
    StartProductionRequest,
    UpdateQuoteRequest,
)
from src.verticals.retail.furniture.service import FurnitureService

router = APIRouter(prefix="/furniture", tags=["furniture"])


@router.get(
    "/custom-orders",
    response_model=list[CustomOrderRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_custom_orders(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    customer_id: UUID | None = Query(default=None, alias="customerId"),
    status_filter: CustomOrderStatus | None = Query(default=None, alias="status"),
) -> list[CustomOrderRead]:
    service = FurnitureService(db)
    if customer_id is not None:
        rows = await service.list_for_customer(
            tenant_id=user.tenant_id, customer_id=customer_id
        )
    elif status_filter is not None:
        rows = await service.list_by_status(
            tenant_id=user.tenant_id, status=status_filter
        )
    else:
        # No filter — fall back to "everything currently on the shop floor",
        # i.e. not delivered and not cancelled. A pure dump is rarely useful.
        rows = [
            row
            for s in (
                CustomOrderStatus.QUOTED,
                CustomOrderStatus.IN_PRODUCTION,
                CustomOrderStatus.READY,
            )
            for row in await service.list_by_status(tenant_id=user.tenant_id, status=s)
        ]
    return [CustomOrderRead.model_validate(r) for r in rows]


@router.post(
    "/custom-orders",
    response_model=CustomOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def quote_order(
    req: QuoteRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).quote(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        description=req.description,
        quoted_price_cents=req.quoted_price_cents,
        customer_id=req.customer_id,
        dimensions_cm=req.dimensions_cm,
        material=req.material,
        finish=req.finish,
        estimated_ready_on=req.estimated_ready_on,
    )
    return CustomOrderRead.model_validate(row)


@router.get(
    "/custom-orders/{order_id}",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_custom_order(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).get(tenant_id=user.tenant_id, order_id=order_id)
    return CustomOrderRead.model_validate(row)


@router.patch(
    "/custom-orders/{order_id}",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_custom_order(
    order_id: UUID,
    req: UpdateQuoteRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).update_quote(
        tenant_id=user.tenant_id,
        order_id=order_id,
        description=req.description,
        quoted_price_cents=req.quoted_price_cents,
        dimensions_cm=req.dimensions_cm,
        material=req.material,
        finish=req.finish,
        estimated_ready_on=req.estimated_ready_on,
    )
    return CustomOrderRead.model_validate(row)


@router.post(
    "/custom-orders/{order_id}/start-production",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def start_production(
    order_id: UUID,
    req: StartProductionRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).start_production(
        tenant_id=user.tenant_id,
        order_id=order_id,
        estimated_ready_on=req.estimated_ready_on,
    )
    return CustomOrderRead.model_validate(row)


@router.post(
    "/custom-orders/{order_id}/mark-ready",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_ready(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).mark_ready(
        tenant_id=user.tenant_id, order_id=order_id
    )
    return CustomOrderRead.model_validate(row)


@router.post(
    "/custom-orders/{order_id}/mark-delivered",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_delivered(
    order_id: UUID,
    req: MarkDeliveredRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).mark_delivered(
        tenant_id=user.tenant_id,
        order_id=order_id,
        paid_order_id=req.order_id,
    )
    return CustomOrderRead.model_validate(row)


@router.post(
    "/custom-orders/{order_id}/cancel",
    response_model=CustomOrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_VOID))],
)
async def cancel_order(
    order_id: UUID,
    req: CancelRequest,  # noqa: ARG001 — reason captured for audit, not stored on the row
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomOrderRead:
    row = await FurnitureService(db).cancel(
        tenant_id=user.tenant_id, order_id=order_id
    )
    return CustomOrderRead.model_validate(row)
