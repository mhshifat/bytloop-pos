from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.grocery.entity import SellUnit
from src.verticals.retail.grocery.schemas import (
    PluCreate,
    PluLookupResponse,
    PluRead,
    ScanRequest,
    ScanResponse,
    WeighableRead,
    WeighableUpsert,
    WeightPriceRequest,
    WeightPriceResponse,
)
from src.verticals.retail.grocery.service import GroceryService

router = APIRouter(prefix="/grocery", tags=["grocery"])


@router.get(
    "/plu/{code}",
    response_model=PluLookupResponse,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def lookup_plu(
    code: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PluLookupResponse:
    product_id = await GroceryService(db).lookup_by_plu(
        tenant_id=user.tenant_id, code=code
    )
    return PluLookupResponse(product_id=product_id)


@router.post(
    "/plu",
    response_model=PluRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def register_plu(
    data: PluCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PluRead:
    plu = await GroceryService(db).register_plu(
        tenant_id=user.tenant_id, code=data.code, product_id=data.product_id
    )
    return PluRead.model_validate(plu)


@router.post(
    "/weigh",
    response_model=WeightPriceResponse,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def weigh(
    req: WeightPriceRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> WeightPriceResponse:
    price = await GroceryService(db).price_by_weight(
        tenant_id=user.tenant_id, product_id=req.product_id, grams=req.grams
    )
    return WeightPriceResponse(price_cents=price)


@router.put(
    "/weighables",
    response_model=WeighableRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_weighable(
    data: WeighableUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> WeighableRead:
    sku = await GroceryService(db).upsert_weighable(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        sell_unit=SellUnit(data.sell_unit),
        price_per_unit_cents=data.price_per_unit_cents,
        tare_grams=data.tare_grams,
    )
    return WeighableRead.model_validate(sku)


@router.post(
    "/scan",
    response_model=ScanResponse,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def scan(
    req: ScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ScanResponse:
    """Register scanner: resolves a PLU (produce) or price-embedded EAN-13
    (from a deli scale) into (product_id, line_total_cents?)."""
    product_id, line_total = await GroceryService(db).resolve_scan(
        tenant_id=user.tenant_id, input_code=req.input_code
    )
    return ScanResponse(product_id=product_id, line_total_cents=line_total)
