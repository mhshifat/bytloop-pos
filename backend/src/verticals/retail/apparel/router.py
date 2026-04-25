from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import NotFoundError
from src.core.permissions import Permission
from src.verticals.retail.apparel.schemas import (
    ApparelVariantRead,
    GenerateMatrixRequest,
    VariantStockAdjust,
    VariantUpdateRequest,
)
from src.verticals.retail.apparel.service import ApparelService

router = APIRouter(prefix="/apparel", tags=["apparel"])


@router.get(
    "/products/{product_id}/variants",
    response_model=list[ApparelVariantRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_variants(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ApparelVariantRead]:
    rows = await ApparelService(db).list_for_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return [ApparelVariantRead.model_validate(r) for r in rows]


@router.post(
    "/variants/generate-matrix",
    response_model=list[ApparelVariantRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def generate_matrix(
    req: GenerateMatrixRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ApparelVariantRead]:
    rows = await ApparelService(db).bulk_create(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        sizes=req.sizes,
        colors=req.colors,
        sku_prefix=req.sku_prefix,
    )
    return [ApparelVariantRead.model_validate(r) for r in rows]


@router.get(
    "/variants/lookup",
    response_model=ApparelVariantRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def lookup_variant(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    barcode: str | None = Query(default=None),
    sku: str | None = Query(default=None),
) -> ApparelVariantRead:
    """Scanner endpoint — resolve a barcode or SKU to a specific variant."""
    service = ApparelService(db)
    variant = None
    if barcode:
        variant = await service.find_by_barcode(tenant_id=user.tenant_id, barcode=barcode)
    elif sku:
        variant = await service.find_by_sku(tenant_id=user.tenant_id, sku=sku)
    if variant is None:
        raise NotFoundError("Variant not found.")
    return ApparelVariantRead.model_validate(variant)


@router.patch(
    "/variants/{variant_id}",
    response_model=ApparelVariantRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def update_variant(
    variant_id: UUID,
    req: VariantUpdateRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ApparelVariantRead:
    variant = await ApparelService(db).update_variant(
        tenant_id=user.tenant_id,
        variant_id=variant_id,
        barcode=req.barcode,
        gender=req.gender,
        fit=req.fit,
        material=req.material,
        price_cents_override=req.price_cents_override,
    )
    return ApparelVariantRead.model_validate(variant)


@router.post(
    "/variants/{variant_id}/stock-adjust",
    response_model=ApparelVariantRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def adjust_variant_stock(
    variant_id: UUID,
    req: VariantStockAdjust,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ApparelVariantRead:
    variant = await ApparelService(db).adjust_variant_stock(
        tenant_id=user.tenant_id, variant_id=variant_id, delta=req.delta
    )
    return ApparelVariantRead.model_validate(variant)
