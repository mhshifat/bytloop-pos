from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.consignment.entity import ConsignmentItemStatus
from src.verticals.retail.consignment.schemas import (
    AddItemRequest,
    ConsignmentItemRead,
    ConsignorPayoutRead,
    ConsignorRead,
    CreateConsignorRequest,
    MarkSoldRequest,
    PayoutRequest,
)
from src.verticals.retail.consignment.service import ConsignmentService

router = APIRouter(prefix="/consignment", tags=["consignment"])


# ── consignors ────────────────────────────────────────────────────


@router.get(
    "/consignors",
    response_model=list[ConsignorRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_consignors(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ConsignorRead]:
    rows = await ConsignmentService(db).list_consignors(tenant_id=user.tenant_id)
    return [ConsignorRead.model_validate(r) for r in rows]


@router.post(
    "/consignors",
    response_model=ConsignorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_consignor(
    req: CreateConsignorRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ConsignorRead:
    consignor = await ConsignmentService(db).create_consignor(
        tenant_id=user.tenant_id,
        name=req.name,
        email=req.email,
        phone=req.phone,
        payout_rate_pct=req.payout_rate_pct,
    )
    return ConsignorRead.model_validate(consignor)


# ── items ─────────────────────────────────────────────────────────


@router.get(
    "/items",
    response_model=list[ConsignmentItemRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_items(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    consignor_id: UUID | None = Query(default=None, alias="consignorId"),
    status_filter: ConsignmentItemStatus | None = Query(default=None, alias="status"),
) -> list[ConsignmentItemRead]:
    rows = await ConsignmentService(db).list_items(
        tenant_id=user.tenant_id,
        consignor_id=consignor_id,
        status=status_filter,
    )
    return [ConsignmentItemRead.model_validate(r) for r in rows]


@router.post(
    "/items",
    response_model=ConsignmentItemRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def add_item(
    req: AddItemRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ConsignmentItemRead:
    item = await ConsignmentService(db).add_item(
        tenant_id=user.tenant_id,
        consignor_id=req.consignor_id,
        product_id=req.product_id,
        listed_price_cents=req.listed_price_cents,
    )
    return ConsignmentItemRead.model_validate(item)


@router.post(
    "/items/{item_id}/mark-sold",
    response_model=ConsignmentItemRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_sold(
    item_id: UUID,
    req: MarkSoldRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ConsignmentItemRead:
    item = await ConsignmentService(db).mark_sold(
        tenant_id=user.tenant_id,
        item_id=item_id,
        sold_price_cents=req.sold_price_cents,
        order_id=req.order_id,
    )
    return ConsignmentItemRead.model_validate(item)


@router.post(
    "/items/{item_id}/return",
    response_model=ConsignmentItemRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def return_item(
    item_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ConsignmentItemRead:
    item = await ConsignmentService(db).mark_returned(
        tenant_id=user.tenant_id, item_id=item_id
    )
    return ConsignmentItemRead.model_validate(item)


# ── payouts ───────────────────────────────────────────────────────


@router.post(
    "/consignors/{consignor_id}/payouts",
    response_model=ConsignorPayoutRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_payout(
    consignor_id: UUID,
    req: PayoutRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ConsignorPayoutRead:
    payout = await ConsignmentService(db).pay_out(
        tenant_id=user.tenant_id,
        consignor_id=consignor_id,
        amount_cents=req.amount_cents,
        note=req.note,
    )
    return ConsignorPayoutRead.model_validate(payout)


@router.get(
    "/consignors/{consignor_id}/payouts",
    response_model=list[ConsignorPayoutRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_payouts(
    consignor_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ConsignorPayoutRead]:
    rows = await ConsignmentService(db).list_payouts(
        tenant_id=user.tenant_id, consignor_id=consignor_id
    )
    return [ConsignorPayoutRead.model_validate(r) for r in rows]
