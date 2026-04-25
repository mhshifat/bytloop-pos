from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.procurement.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderItemRead,
    PurchaseOrderList,
    PurchaseOrderRead,
    PurchaseOrderSummary,
    ReceiveRequest,
    SupplierCreate,
    SupplierRead,
)
from src.modules.procurement.service import ProcurementService

suppliers_router = APIRouter(prefix="/suppliers", tags=["procurement"])
purchase_orders_router = APIRouter(prefix="/purchase-orders", tags=["procurement"])


@suppliers_router.get(
    "",
    response_model=list[SupplierRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_suppliers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SupplierRead]:
    rows = await ProcurementService(db).list_suppliers(tenant_id=user.tenant_id)
    return [SupplierRead.model_validate(r) for r in rows]


@suppliers_router.post(
    "",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_supplier(
    data: SupplierCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SupplierRead:
    supplier = await ProcurementService(db).create_supplier(
        tenant_id=user.tenant_id, actor_id=user.id, data=data
    )
    return SupplierRead.model_validate(supplier)


@purchase_orders_router.get(
    "",
    response_model=PurchaseOrderList,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_purchase_orders(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100, alias="pageSize"),
) -> PurchaseOrderList:
    rows, has_more = await ProcurementService(db).list_purchase_orders(
        tenant_id=user.tenant_id, page=page, page_size=page_size
    )
    return PurchaseOrderList(
        items=[
            PurchaseOrderSummary(
                id=po.id,
                supplier_id=po.supplier_id,
                number=po.number,
                status=po.status,
                total_cents=po.total_cents,
                currency=po.currency,
                created_at=po.created_at,
            )
            for po in rows
        ],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )


@purchase_orders_router.post(
    "",
    response_model=PurchaseOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PurchaseOrderRead:
    po, items = await ProcurementService(db).create_purchase_order(
        tenant_id=user.tenant_id, actor_id=user.id, data=data
    )
    return PurchaseOrderRead(
        id=po.id,
        supplier_id=po.supplier_id,
        number=po.number,
        status=po.status,
        total_cents=po.total_cents,
        currency=po.currency,
        created_at=po.created_at,
        sent_at=po.sent_at,
        closed_at=po.closed_at,
        items=[PurchaseOrderItemRead.model_validate(i) for i in items],
    )


@purchase_orders_router.get(
    "/{purchase_order_id}",
    response_model=PurchaseOrderRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_purchase_order(
    purchase_order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PurchaseOrderRead:
    po, items = await ProcurementService(db).get_purchase_order(
        tenant_id=user.tenant_id, purchase_order_id=purchase_order_id
    )
    return PurchaseOrderRead(
        id=po.id,
        supplier_id=po.supplier_id,
        number=po.number,
        status=po.status,
        total_cents=po.total_cents,
        currency=po.currency,
        created_at=po.created_at,
        sent_at=po.sent_at,
        closed_at=po.closed_at,
        items=[PurchaseOrderItemRead.model_validate(i) for i in items],
    )


@purchase_orders_router.post(
    "/{purchase_order_id}/receive",
    response_model=PurchaseOrderRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def receive_purchase_order(
    purchase_order_id: UUID,
    req: ReceiveRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PurchaseOrderRead:
    service = ProcurementService(db)
    po = await service.receive(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        purchase_order_id=purchase_order_id,
        received=req.items,
    )
    _, items = await service.get_purchase_order(
        tenant_id=user.tenant_id, purchase_order_id=po.id
    )
    return PurchaseOrderRead(
        id=po.id,
        supplier_id=po.supplier_id,
        number=po.number,
        status=po.status,
        total_cents=po.total_cents,
        currency=po.currency,
        created_at=po.created_at,
        sent_at=po.sent_at,
        closed_at=po.closed_at,
        items=[PurchaseOrderItemRead.model_validate(i) for i in items],
    )
