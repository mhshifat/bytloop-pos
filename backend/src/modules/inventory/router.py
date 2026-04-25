from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.inventory.schemas import (
    InventoryLevelList,
    InventoryLevelRead,
    LocationCreate,
    LocationRead,
    ReorderPointRequest,
    StockAdjustRequest,
    TransferRequest,
    TransferResult,
)
from src.modules.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])
locations_router = APIRouter(prefix="/locations", tags=["inventory"])


@router.get(
    "/levels",
    response_model=InventoryLevelList,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_levels(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200, alias="pageSize"),
) -> InventoryLevelList:
    rows, has_more = await InventoryService(db).list_levels(
        tenant_id=user.tenant_id, page=page, page_size=page_size
    )
    return InventoryLevelList(
        items=[
            InventoryLevelRead(
                id=level.id,
                product_id=level.product_id,
                product_name=name,
                sku=sku,
                location_id=level.location_id,
                location_code=loc_code,
                location_name=loc_name,
                quantity=level.quantity,
                reorder_point=level.reorder_point,
                updated_at=level.updated_at,
            )
            for level, name, sku, loc_code, loc_name in rows
        ],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )


@locations_router.get(
    "",
    response_model=list[LocationRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_locations(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[LocationRead]:
    rows = await InventoryService(db).list_locations(tenant_id=user.tenant_id)
    return [LocationRead.model_validate(r) for r in rows]


@router.post(
    "/adjust",
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def adjust_stock(
    data: StockAdjustRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, int]:
    new_qty = await InventoryService(db).manual_adjust(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        delta=data.delta,
    )
    return {"quantity": new_qty}


@router.post(
    "/transfer",
    response_model=TransferResult,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def transfer_stock(
    data: TransferRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransferResult:
    source_qty, dest_qty = await InventoryService(db).transfer_stock(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        source_location_id=data.source_location_id,
        destination_location_id=data.destination_location_id,
        quantity=data.quantity,
    )
    return TransferResult(source_quantity=source_qty, destination_quantity=dest_qty)


@router.post(
    "/reorder-point",
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def set_reorder_point(
    data: ReorderPointRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, int]:
    value = await InventoryService(db).set_reorder_point(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        reorder_point=data.reorder_point,
    )
    return {"reorderPoint": value}


@locations_router.post(
    "",
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_location(
    data: LocationCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LocationRead:
    loc = await InventoryService(db).create_location(
        tenant_id=user.tenant_id, code=data.code, name=data.name
    )
    return LocationRead.model_validate(loc)
