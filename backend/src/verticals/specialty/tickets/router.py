from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.tickets.schemas import (
    EventCreate,
    EventRead,
    IssuedTicketRead,
    PurchaseTicketsRequest,
    ScanRequest,
    TicketTypeCreate,
    TicketTypeRead,
    VoidRequest,
)
from src.verticals.specialty.tickets.service import TicketsService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get(
    "/events",
    response_model=list[EventRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_events(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[EventRead]:
    rows = await TicketsService(db).list_events(tenant_id=user.tenant_id)
    return [EventRead.model_validate(e) for e in rows]


@router.post(
    "/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_event(
    data: EventCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> EventRead:
    event = await TicketsService(db).create_event(
        tenant_id=user.tenant_id,
        title=data.title,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        venue=data.venue,
    )
    return EventRead.model_validate(event)


@router.post(
    "/events/{event_id}/cancel",
    response_model=EventRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def cancel_event(
    event_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> EventRead:
    event = await TicketsService(db).cancel_event(
        tenant_id=user.tenant_id, event_id=event_id
    )
    return EventRead.model_validate(event)


@router.get(
    "/events/{event_id}/types",
    response_model=list[TicketTypeRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_ticket_types(
    event_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[TicketTypeRead]:
    rows = await TicketsService(db).list_ticket_types(
        tenant_id=user.tenant_id, event_id=event_id
    )
    return [TicketTypeRead.model_validate(r) for r in rows]


@router.post(
    "/events/{event_id}/types",
    response_model=TicketTypeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def add_ticket_type(
    event_id: UUID,
    data: TicketTypeCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TicketTypeRead:
    ticket_type = await TicketsService(db).add_ticket_type(
        tenant_id=user.tenant_id,
        event_id=event_id,
        code=data.code,
        name=data.name,
        price_cents=data.price_cents,
        quota=data.quota,
    )
    return TicketTypeRead.model_validate(ticket_type)


@router.post(
    "/purchase",
    response_model=list[IssuedTicketRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def purchase_tickets(
    data: PurchaseTicketsRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[IssuedTicketRead]:
    tickets = await TicketsService(db).purchase_tickets(
        tenant_id=user.tenant_id,
        ticket_type_id=data.ticket_type_id,
        quantity=data.quantity,
        order_id=data.order_id,
        holder_names=list(data.holder_names),
    )
    return [IssuedTicketRead.model_validate(t) for t in tickets]


@router.post(
    "/scan",
    response_model=IssuedTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def scan_ticket(
    data: ScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> IssuedTicketRead:
    ticket = await TicketsService(db).scan(
        tenant_id=user.tenant_id, serial_no=data.serial_no
    )
    return IssuedTicketRead.model_validate(ticket)


@router.post(
    "/void",
    response_model=IssuedTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_VOID))],
)
async def void_ticket(
    data: VoidRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> IssuedTicketRead:
    ticket = await TicketsService(db).void(
        tenant_id=user.tenant_id, serial_no=data.serial_no
    )
    return IssuedTicketRead.model_validate(ticket)


@router.get(
    "/types/{ticket_type_id}/issued",
    response_model=list[IssuedTicketRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_issued(
    ticket_type_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[IssuedTicketRead]:
    rows = await TicketsService(db).list_issued(
        tenant_id=user.tenant_id, ticket_type_id=ticket_type_id
    )
    return [IssuedTicketRead.model_validate(r) for r in rows]
