from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.restaurant.entity import KdsStation
from src.verticals.fnb.restaurant.schemas import (
    FireKotRequest,
    FireOrderRequest,
    KotTicketRead,
    RouteRead,
    RouteUpsertRequest,
    TableCreate,
    TableRead,
    UpdateKotStatusRequest,
)
from src.verticals.fnb.restaurant.service import RestaurantService

router = APIRouter(prefix="/restaurant", tags=["restaurant"])


@router.get(
    "/tables",
    response_model=list[TableRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_tables(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[TableRead]:
    tables = await RestaurantService(db).list_tables(tenant_id=user.tenant_id)
    return [TableRead.model_validate(t) for t in tables]


@router.post(
    "/tables",
    response_model=TableRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_table(
    data: TableCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TableRead:
    table = await RestaurantService(db).create_table(tenant_id=user.tenant_id, data=data)
    return TableRead.model_validate(table)


@router.post(
    "/kot/fire",
    response_model=KotTicketRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def fire_kot(
    req: FireKotRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> KotTicketRead:
    ticket = await RestaurantService(db).fire_kot(
        tenant_id=user.tenant_id,
        order_id=req.order_id,
        station=req.station,
        items=req.items,
        course=req.course,
    )
    return KotTicketRead.model_validate(ticket)


@router.post(
    "/kot/fire-order",
    response_model=list[KotTicketRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def fire_order(
    req: FireOrderRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[KotTicketRead]:
    """Auto-route items to stations via product_station_routes; one ticket per station/course."""
    tickets = await RestaurantService(db).fire_order(
        tenant_id=user.tenant_id, order_id=req.order_id, items=req.items
    )
    return [KotTicketRead.model_validate(t) for t in tickets]


@router.get(
    "/routes",
    response_model=list[RouteRead],
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def list_routes(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[RouteRead]:
    routes = await RestaurantService(db).list_routes(tenant_id=user.tenant_id)
    return [RouteRead.model_validate(r) for r in routes]


@router.put(
    "/routes",
    response_model=RouteRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_route(
    req: RouteUpsertRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RouteRead:
    route = await RestaurantService(db).upsert_route(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        station=req.station,
        course=req.course,
    )
    return RouteRead.model_validate(route)


@router.get(
    "/kds",
    response_model=list[KotTicketRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def kds_queue(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    station: KdsStation = Query(default=KdsStation.KITCHEN),
) -> list[KotTicketRead]:
    tickets = await RestaurantService(db).list_station_tickets(
        tenant_id=user.tenant_id, station=station
    )
    return [KotTicketRead.model_validate(t) for t in tickets]


@router.patch(
    "/kot/{ticket_id}/status",
    response_model=KotTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_kot_status(
    ticket_id: UUID,
    req: UpdateKotStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> KotTicketRead:
    ticket = await RestaurantService(db).update_kot_status(
        tenant_id=user.tenant_id, ticket_id=ticket_id, status=req.status
    )
    return KotTicketRead.model_validate(ticket)
