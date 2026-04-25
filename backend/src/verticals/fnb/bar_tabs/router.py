from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.bar_tabs.schemas import (
    AddLineRequest,
    BarTabLineRead,
    BarTabRead,
    CloseTabRequest,
    OpenTabRequest,
)
from src.verticals.fnb.bar_tabs.service import BarTabService

router = APIRouter(prefix="/bar-tabs", tags=["bar-tabs"])


async def _to_read(svc: BarTabService, *, tenant_id: UUID, tab) -> BarTabRead:  # type: ignore[no-untyped-def]
    lines = await svc.list_lines(tenant_id=tenant_id, tab_id=tab.id)
    return BarTabRead(
        id=tab.id,
        customer_id=tab.customer_id,
        status=tab.status,
        preauth_reference=tab.preauth_reference,
        opened_at=tab.opened_at,
        closed_at=tab.closed_at,
        order_id=tab.order_id,
        total_cents=tab.total_cents,
        lines=[BarTabLineRead.model_validate(line) for line in lines],
    )


@router.post(
    "",
    response_model=BarTabRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def open_tab(
    data: OpenTabRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BarTabRead:
    svc = BarTabService(db)
    tab = await svc.open_tab(
        tenant_id=user.tenant_id,
        opened_by_user_id=user.id,
        customer_id=data.customer_id,
        preauth_reference=data.preauth_reference,
    )
    return await _to_read(svc, tenant_id=user.tenant_id, tab=tab)


@router.get(
    "",
    response_model=list[BarTabRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_open_tabs(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BarTabRead]:
    svc = BarTabService(db)
    tabs = await svc.list_open_tabs(tenant_id=user.tenant_id)
    return [await _to_read(svc, tenant_id=user.tenant_id, tab=t) for t in tabs]


@router.get(
    "/{tab_id}",
    response_model=BarTabRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_tab(
    tab_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BarTabRead:
    svc = BarTabService(db)
    tab = await svc.get(tenant_id=user.tenant_id, tab_id=tab_id)
    return await _to_read(svc, tenant_id=user.tenant_id, tab=tab)


@router.post(
    "/{tab_id}/lines",
    response_model=BarTabRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def add_line(
    tab_id: UUID,
    data: AddLineRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BarTabRead:
    svc = BarTabService(db)
    await svc.add_line(
        tenant_id=user.tenant_id,
        tab_id=tab_id,
        product_id=data.product_id,
        quantity=data.quantity,
        unit_price_cents=data.unit_price_cents,
    )
    tab = await svc.get(tenant_id=user.tenant_id, tab_id=tab_id)
    return await _to_read(svc, tenant_id=user.tenant_id, tab=tab)


@router.post(
    "/{tab_id}/close",
    response_model=BarTabRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def close_tab(
    tab_id: UUID,
    _: CloseTabRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BarTabRead:
    svc = BarTabService(db)
    tab = await svc.close_tab(
        tenant_id=user.tenant_id, cashier_id=user.id, tab_id=tab_id
    )
    return await _to_read(svc, tenant_id=user.tenant_id, tab=tab)


@router.post(
    "/{tab_id}/abandon",
    response_model=BarTabRead,
    dependencies=[Depends(requires(Permission.ORDERS_VOID))],
)
async def abandon_tab(
    tab_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BarTabRead:
    svc = BarTabService(db)
    tab = await svc.abandon_tab(tenant_id=user.tenant_id, tab_id=tab_id)
    return await _to_read(svc, tenant_id=user.tenant_id, tab=tab)
