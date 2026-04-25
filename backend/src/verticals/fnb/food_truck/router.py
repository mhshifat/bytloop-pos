from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.food_truck.schemas import (
    DailyMenuItemRead,
    DailyMenuRead,
    MarkSoldOutRequest,
    PublishMenuRequest,
    SetLocationRequest,
    TruckLocationRead,
)
from src.verticals.fnb.food_truck.service import FoodTruckService

router = APIRouter(prefix="/food-truck", tags=["food-truck"])


# ──────────────────────────────────────────────
# Locations
# ──────────────────────────────────────────────


@router.post(
    "/locations",
    response_model=TruckLocationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def set_location(
    data: SetLocationRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TruckLocationRead:
    location = await FoodTruckService(db).set_location(
        tenant_id=user.tenant_id,
        location_name=data.location_name,
        latitude=data.latitude,
        longitude=data.longitude,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        notes=data.notes,
    )
    return TruckLocationRead.model_validate(location)


@router.get(
    "/locations",
    response_model=list[TruckLocationRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_locations(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    upcoming_only: bool = Query(default=False),
) -> list[TruckLocationRead]:
    locations = await FoodTruckService(db).list_locations(
        tenant_id=user.tenant_id, upcoming_only=upcoming_only
    )
    return [TruckLocationRead.model_validate(loc) for loc in locations]


@router.get(
    "/locations/current",
    response_model=TruckLocationRead | None,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def current_location(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TruckLocationRead | None:
    location = await FoodTruckService(db).current_location(tenant_id=user.tenant_id)
    return TruckLocationRead.model_validate(location) if location else None


# ──────────────────────────────────────────────
# Daily menu
# ──────────────────────────────────────────────


@router.post(
    "/menus",
    response_model=DailyMenuRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def publish_menu(
    data: PublishMenuRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DailyMenuRead:
    svc = FoodTruckService(db)
    menu = await svc.publish_menu(
        tenant_id=user.tenant_id,
        menu_date=data.menu_date,
        items=data.items,
        notes=data.notes,
    )
    items = await svc.list_menu_items(tenant_id=user.tenant_id, menu_id=menu.id)
    return DailyMenuRead(
        id=menu.id,
        menu_date=menu.menu_date,
        notes=menu.notes,
        published_at=menu.published_at,
        items=[DailyMenuItemRead.model_validate(i) for i in items],
    )


@router.get(
    "/menus/today",
    response_model=DailyMenuRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def today_menu(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DailyMenuRead:
    menu, items = await FoodTruckService(db).today_menu(tenant_id=user.tenant_id)
    return DailyMenuRead(
        id=menu.id,
        menu_date=menu.menu_date,
        notes=menu.notes,
        published_at=menu.published_at,
        items=[DailyMenuItemRead.model_validate(i) for i in items],
    )


@router.patch(
    "/menu-items/{item_id}/sold-out",
    response_model=DailyMenuItemRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_sold_out(
    item_id: UUID,
    data: MarkSoldOutRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DailyMenuItemRead:
    item = await FoodTruckService(db).mark_sold_out(
        tenant_id=user.tenant_id, item_id=item_id, sold_out=data.sold_out
    )
    return DailyMenuItemRead.model_validate(item)
