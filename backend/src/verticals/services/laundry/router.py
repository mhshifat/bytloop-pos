from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.laundry.entity import LaundryStatus
from src.verticals.services.laundry.schemas import (
    LaundryItemCreate,
    LaundryItemRead,
    LaundryTicketCreate,
    LaundryTicketRead,
    MarkCollectedRequest,
)
from src.verticals.services.laundry.service import LaundryService

router = APIRouter(prefix="/laundry", tags=["laundry"])


@router.get(
    "/tickets",
    response_model=list[LaundryTicketRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_tickets(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    status_filter: LaundryStatus | None = Query(default=None, alias="status"),
) -> list[LaundryTicketRead]:
    rows = await LaundryService(db).list_tickets(
        tenant_id=user.tenant_id, status=status_filter
    )
    return [LaundryTicketRead.model_validate(r) for r in rows]


@router.post(
    "/tickets",
    response_model=LaundryTicketRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_ticket(
    data: LaundryTicketCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LaundryTicketRead:
    ticket = await LaundryService(db).create_ticket(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        ticket_no=data.ticket_no,
        item_count=data.item_count,
        promised_at=data.promised_at,
    )
    return LaundryTicketRead.model_validate(ticket)


@router.get(
    "/tickets/{ticket_id}",
    response_model=LaundryTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_ticket(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LaundryTicketRead:
    ticket = await LaundryService(db).get_ticket(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return LaundryTicketRead.model_validate(ticket)


@router.get(
    "/tickets/{ticket_id}/items",
    response_model=list[LaundryItemRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_items(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[LaundryItemRead]:
    rows = await LaundryService(db).list_items(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return [LaundryItemRead.model_validate(r) for r in rows]


@router.post(
    "/tickets/{ticket_id}/items",
    response_model=list[LaundryItemRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def add_items(
    ticket_id: UUID,
    data: list[LaundryItemCreate],
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[LaundryItemRead]:
    items = await LaundryService(db).add_items(
        tenant_id=user.tenant_id,
        ticket_id=ticket_id,
        items=[
            {
                "description": d.description,
                "quantity": d.quantity,
                "service_type": d.service_type,
                "price_cents": d.price_cents,
            }
            for d in data
        ],
    )
    return [LaundryItemRead.model_validate(i) for i in items]


@router.post(
    "/tickets/{ticket_id}/ready",
    response_model=LaundryTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_ready(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LaundryTicketRead:
    ticket = await LaundryService(db).mark_ready(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return LaundryTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/collect",
    response_model=LaundryTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_collected(
    ticket_id: UUID,
    data: MarkCollectedRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LaundryTicketRead:
    ticket = await LaundryService(db).mark_collected(
        tenant_id=user.tenant_id,
        ticket_id=ticket_id,
        order_id=data.order_id,
    )
    return LaundryTicketRead.model_validate(ticket)
