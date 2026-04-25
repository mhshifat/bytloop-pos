from __future__ import annotations

from uuid import UUID

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.sales.entity import OrderStatus
from src.modules.sales.schemas import (
    CheckoutRequest,
    OrderItemRead,
    OrderList,
    OrderRead,
    OrderSummary,
    PaymentRead,
)
from src.modules.sales.service import CompletedSale, SalesService

router = APIRouter(prefix="/orders", tags=["sales"])


def _to_response(sale: CompletedSale) -> OrderRead:
    return OrderRead(
        id=sale.order.id,
        number=sale.order.number,
        order_type=sale.order.order_type,
        status=sale.order.status,
        currency=sale.order.currency,
        subtotal_cents=sale.order.subtotal_cents,
        tax_cents=sale.order.tax_cents,
        discount_cents=sale.order.discount_cents,
        total_cents=sale.order.total_cents,
        customer_id=sale.order.customer_id,
        items=[
            OrderItemRead(
                id=i.id,
                product_id=i.product_id,
                name_snapshot=i.name_snapshot,
                unit_price_cents=i.unit_price_cents,
                quantity=i.quantity,
                line_total_cents=i.line_total_cents,
                vertical_data=dict(i.vertical_data or {}),
            )
            for i in sale.items
        ],
        payments=[
            PaymentRead(id=p.id, method=p.method, amount_cents=p.amount_cents, currency=p.currency)
            for p in sale.payments
        ],
        change_due_cents=sale.change_due_cents,
    )


@router.post(
    "/checkout",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def checkout(
    req: CheckoutRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> OrderRead:
    sale = await SalesService(db).checkout(
        tenant_id=user.tenant_id,
        cashier_id=user.id,
        items=req.items,
        order_type=req.order_type,
        payment_method=req.payment_method,
        amount_tendered_cents=req.amount_tendered_cents,
        customer_id=req.customer_id,
        discount_code=req.discount_code,
        payment_reference=req.payment_reference,
        order_vertical_data=req.order_vertical_data,
        age_verification=req.age_verification,
    )
    return _to_response(sale)


@router.get(
    "",
    response_model=OrderList,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_orders(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100, alias="pageSize"),
    status: OrderStatus | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> OrderList:
    rows, has_more = await SalesService(db).list_orders(
        tenant_id=user.tenant_id,
        page=page,
        page_size=page_size,
        status=status,
        since=since,
        until=until,
    )
    return OrderList(
        items=[
            OrderSummary(
                id=o.id,
                number=o.number,
                status=o.status,
                order_type=o.order_type,
                currency=o.currency,
                total_cents=o.total_cents,
                customer_id=o.customer_id,
                opened_at=o.opened_at,
                closed_at=o.closed_at,
            )
            for o in rows
        ],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/export.csv",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def export_orders_csv(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> StreamingResponse:
    # Stream all matching orders — no pagination for export. Backed by the
    # same repo.list filter as the HTML list, with a large limit.
    rows, _ = await SalesService(db).list_orders(
        tenant_id=user.tenant_id,
        page=1,
        page_size=10_000,
        status=status_filter,
        since=since,
        until=until,
    )

    def generate() -> "Iterator[str]":  # type: ignore[name-defined]
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "number",
                "status",
                "order_type",
                "currency",
                "subtotal_cents",
                "tax_cents",
                "discount_cents",
                "total_cents",
                "opened_at",
                "closed_at",
            ]
        )
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for order in rows:
            writer.writerow(
                [
                    order.number,
                    order.status.value if hasattr(order.status, "value") else order.status,
                    order.order_type.value if hasattr(order.order_type, "value") else order.order_type,
                    order.currency,
                    order.subtotal_cents,
                    order.tax_cents,
                    order.discount_cents,
                    order.total_cents,
                    order.opened_at.isoformat(),
                    order.closed_at.isoformat() if order.closed_at else "",
                ]
            )
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"orders-{datetime.utcnow().date().isoformat()}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_order(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> OrderRead:
    sale = await SalesService(db).get_order(tenant_id=user.tenant_id, order_id=order_id)
    return _to_response(sale)


@router.post(
    "/{order_id}/void",
    response_model=OrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_VOID))],
)
async def void_order(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> OrderRead:
    service = SalesService(db)
    await service.void_order(
        tenant_id=user.tenant_id, actor_id=user.id, order_id=order_id
    )
    sale = await service.get_order(tenant_id=user.tenant_id, order_id=order_id)
    return _to_response(sale)


@router.post(
    "/{order_id}/refund",
    response_model=OrderRead,
    dependencies=[Depends(requires(Permission.ORDERS_REFUND))],
)
async def refund_order(
    order_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> OrderRead:
    service = SalesService(db)
    await service.refund_order(
        tenant_id=user.tenant_id, actor_id=user.id, order_id=order_id
    )
    sale = await service.get_order(tenant_id=user.tenant_id, order_id=order_id)
    return _to_response(sale)
