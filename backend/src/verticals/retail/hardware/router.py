from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.hardware.schemas import (
    QuantityBreakRead,
    ResolvedPrice,
    ResolvePriceRequest,
    SetBreaksRequest,
)
from src.verticals.retail.hardware.service import HardwareService

router = APIRouter(prefix="/hardware", tags=["hardware"])


@router.get(
    "/quantity-breaks",
    response_model=list[QuantityBreakRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_quantity_breaks(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID = Query(..., alias="productId"),
) -> list[QuantityBreakRead]:
    rows = await HardwareService(db).list_for_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return [QuantityBreakRead.model_validate(r) for r in rows]


@router.put(
    "/quantity-breaks",
    response_model=list[QuantityBreakRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def set_quantity_breaks(
    req: SetBreaksRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[QuantityBreakRead]:
    rows = await HardwareService(db).set_breaks(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        tiers=[(t.min_quantity, t.unit_price_cents) for t in req.tiers],
    )
    return [QuantityBreakRead.model_validate(r) for r in rows]


@router.post(
    "/quantity-breaks/resolve",
    response_model=ResolvedPrice,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def resolve_unit_price(
    req: ResolvePriceRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ResolvedPrice:
    unit_price, matched = await HardwareService(db).resolve_unit_price(
        tenant_id=user.tenant_id, product_id=req.product_id, quantity=req.quantity
    )
    return ResolvedPrice(
        product_id=req.product_id,
        quantity=req.quantity,
        unit_price_cents=unit_price,
        matched_min_quantity=matched,
    )
