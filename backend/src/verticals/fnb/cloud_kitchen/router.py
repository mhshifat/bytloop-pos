from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.cloud_kitchen.schemas import (
    AttachProductRequest,
    BrandOrderRead,
    BrandProductRead,
    CreateBrandRequest,
    RecordBrandOrderRequest,
    UpdateBrandRequest,
    VirtualBrandRead,
)
from src.verticals.fnb.cloud_kitchen.service import CloudKitchenService

router = APIRouter(prefix="/cloud-kitchen", tags=["cloud-kitchen"])


@router.post(
    "/brands",
    response_model=VirtualBrandRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_brand(
    data: CreateBrandRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VirtualBrandRead:
    brand = await CloudKitchenService(db).create_brand(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        logo_url=data.logo_url,
        is_active=data.is_active,
    )
    return VirtualBrandRead.model_validate(brand)


@router.get(
    "/brands",
    response_model=list[VirtualBrandRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_brands(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    include_inactive: bool = Query(default=False),
) -> list[VirtualBrandRead]:
    brands = await CloudKitchenService(db).list_brands(
        tenant_id=user.tenant_id, include_inactive=include_inactive
    )
    return [VirtualBrandRead.model_validate(b) for b in brands]


@router.get(
    "/brands/{brand_id}",
    response_model=VirtualBrandRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_brand(
    brand_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VirtualBrandRead:
    brand = await CloudKitchenService(db).get_brand(
        tenant_id=user.tenant_id, brand_id=brand_id
    )
    return VirtualBrandRead.model_validate(brand)


@router.patch(
    "/brands/{brand_id}",
    response_model=VirtualBrandRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def update_brand(
    brand_id: UUID,
    data: UpdateBrandRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VirtualBrandRead:
    brand = await CloudKitchenService(db).update_brand(
        tenant_id=user.tenant_id,
        brand_id=brand_id,
        name=data.name,
        logo_url=data.logo_url,
        is_active=data.is_active,
    )
    return VirtualBrandRead.model_validate(brand)


@router.post(
    "/brands/{brand_id}/products",
    response_model=BrandProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def attach_product(
    brand_id: UUID,
    data: AttachProductRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BrandProductRead:
    assoc = await CloudKitchenService(db).attach_product(
        tenant_id=user.tenant_id, brand_id=brand_id, product_id=data.product_id
    )
    return BrandProductRead.model_validate(assoc)


@router.delete(
    "/brands/{brand_id}/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def detach_product(
    brand_id: UUID,
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> None:
    await CloudKitchenService(db).detach_product(
        tenant_id=user.tenant_id, brand_id=brand_id, product_id=product_id
    )


@router.get(
    "/brands/{brand_id}/products",
    response_model=list[BrandProductRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_brand_products(
    brand_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BrandProductRead]:
    rows = await CloudKitchenService(db).list_brand_products(
        tenant_id=user.tenant_id, brand_id=brand_id
    )
    return [BrandProductRead.model_validate(r) for r in rows]


@router.post(
    "/brand-orders",
    response_model=BrandOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def record_brand_order(
    data: RecordBrandOrderRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BrandOrderRead:
    row = await CloudKitchenService(db).record_brand_order(
        tenant_id=user.tenant_id,
        order_id=data.order_id,
        brand_id=data.brand_id,
        external_order_ref=data.external_order_ref,
    )
    return BrandOrderRead.model_validate(row)


@router.get(
    "/brands/{brand_id}/orders",
    response_model=list[BrandOrderRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_brand_orders(
    brand_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BrandOrderRead]:
    rows = await CloudKitchenService(db).list_brand_orders(
        tenant_id=user.tenant_id, brand_id=brand_id
    )
    return [BrandOrderRead.model_validate(r) for r in rows]
