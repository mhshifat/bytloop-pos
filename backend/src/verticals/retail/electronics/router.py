from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import NotFoundError, ValidationError
from src.core.permissions import Permission
from src.verticals.retail.electronics.schemas import (
    ElectronicsItemRead,
    MarkSoldRequest,
    RegisterItemRequest,
    WarrantyStatus,
)
from src.verticals.retail.electronics.service import ElectronicsService

router = APIRouter(prefix="/electronics", tags=["electronics"])


@router.get(
    "/items",
    response_model=list[ElectronicsItemRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_items(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID = Query(..., alias="productId"),
) -> list[ElectronicsItemRead]:
    rows = await ElectronicsService(db).list_for_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return [ElectronicsItemRead.model_validate(r) for r in rows]


@router.post(
    "/items",
    response_model=ElectronicsItemRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def register_item(
    req: RegisterItemRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ElectronicsItemRead:
    item = await ElectronicsService(db).register_item(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        serial_no=req.serial_no,
        imei=req.imei,
        warranty_months=req.warranty_months,
        purchased_on=req.purchased_on,
    )
    return ElectronicsItemRead.model_validate(item)


@router.get(
    "/lookup",
    response_model=ElectronicsItemRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def lookup_item(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    serial: str | None = Query(default=None),
    imei: str | None = Query(default=None),
) -> ElectronicsItemRead:
    """Resolve a serial number or IMEI back to its registered unit."""
    if not serial and not imei:
        raise ValidationError("Provide either 'serial' or 'imei'.")
    service = ElectronicsService(db)
    item = None
    if serial:
        item = await service.lookup_by_serial(tenant_id=user.tenant_id, serial_no=serial)
    elif imei:
        item = await service.lookup_by_imei(tenant_id=user.tenant_id, imei=imei)
    if item is None:
        raise NotFoundError("Electronics item not found.")
    return ElectronicsItemRead.model_validate(item)


@router.post(
    "/items/{item_id}/mark-sold",
    response_model=ElectronicsItemRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_item_sold(
    item_id: UUID,
    req: MarkSoldRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ElectronicsItemRead:
    item = await ElectronicsService(db).mark_sold(
        tenant_id=user.tenant_id, item_id=item_id, order_id=req.order_id
    )
    return ElectronicsItemRead.model_validate(item)


@router.get(
    "/warranty",
    response_model=WarrantyStatus,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def warranty_status(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    serial: str = Query(...),
) -> WarrantyStatus:
    item, days_remaining, expires = await ElectronicsService(db).check_warranty_status(
        tenant_id=user.tenant_id, serial_no=serial
    )
    return WarrantyStatus(
        serial_no=item.serial_no,
        covered=expires is not None and days_remaining >= 0,
        days_remaining=days_remaining,
        warranty_expires_on=expires,
    )
