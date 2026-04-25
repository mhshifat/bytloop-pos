from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.jewelry.schemas import (
    JewelryAttributeRead,
    JewelryAttributeUpsert,
    JewelryQuoteRead,
    MetalRateRead,
    MetalRateUpsert,
)
from src.verticals.specialty.jewelry.service import JewelryService

router = APIRouter(prefix="/jewelry", tags=["jewelry"])


@router.get(
    "/products/{product_id}",
    response_model=JewelryAttributeRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_attributes(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JewelryAttributeRead:
    row = await JewelryService(db).get(tenant_id=user.tenant_id, product_id=product_id)
    return JewelryAttributeRead.model_validate(row)


@router.put(
    "/products/{product_id}",
    response_model=JewelryAttributeRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_attributes(
    product_id: UUID,
    data: JewelryAttributeUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JewelryAttributeRead:
    if data.product_id != product_id:
        data = data.model_copy(update={"product_id": product_id})
    row = await JewelryService(db).upsert_attribute(
        tenant_id=user.tenant_id,
        product_id=product_id,
        metal=data.metal,
        karat=data.karat,
        gross_grams=data.gross_grams,
        net_grams=data.net_grams,
        making_charge_pct=data.making_charge_pct,
        making_charge_per_gram_cents=data.making_charge_per_gram_cents,
        wastage_pct=data.wastage_pct,
        stone_value_cents=data.stone_value_cents,
        certificate_no=data.certificate_no,
    )
    return JewelryAttributeRead.model_validate(row)


@router.get(
    "/rates",
    response_model=list[MetalRateRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_rates(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[MetalRateRead]:
    rows = await JewelryService(db).list_rates(tenant_id=user.tenant_id)
    return [MetalRateRead.model_validate(r) for r in rows]


@router.put(
    "/rates",
    response_model=MetalRateRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_rate(
    data: MetalRateUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> MetalRateRead:
    row = await JewelryService(db).set_rate(
        tenant_id=user.tenant_id,
        metal=data.metal,
        karat=data.karat,
        rate_per_gram_cents=data.rate_per_gram_cents,
        effective_on=data.effective_on,
    )
    return MetalRateRead.model_validate(row)


@router.get(
    "/products/{product_id}/quote",
    response_model=JewelryQuoteRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def quote(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JewelryQuoteRead:
    result = await JewelryService(db).quote(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return JewelryQuoteRead(
        product_id=product_id,
        metal_value_cents=result.metal_value_cents,
        wastage_cents=result.wastage_cents,
        making_charge_cents=result.making_charge_cents,
        stone_value_cents=result.stone_value_cents,
        total_cents=result.total_cents,
    )
