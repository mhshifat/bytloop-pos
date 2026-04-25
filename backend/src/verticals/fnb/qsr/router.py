from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.qsr.entity import DriveThruStatus
from src.verticals.fnb.qsr.schemas import (
    BoardRead,
    CreateTicketRequest,
    DriveThruTicketRead,
)
from src.verticals.fnb.qsr.service import QsrService

router = APIRouter(prefix="/qsr", tags=["qsr"])


@router.post(
    "/tickets",
    response_model=DriveThruTicketRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_ticket(
    data: CreateTicketRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).create_ticket(
        tenant_id=user.tenant_id,
        order_id=data.order_id,
        lane=data.lane,
        estimated_ready_at=data.estimated_ready_at,
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.get(
    "/tickets",
    response_model=list[DriveThruTicketRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_active(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[DriveThruTicketRead]:
    tickets = await QsrService(db).list_active(tenant_id=user.tenant_id)
    return [DriveThruTicketRead.model_validate(t) for t in tickets]


@router.get(
    "/tickets/{ticket_id}",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_ticket(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).get(tenant_id=user.tenant_id, ticket_id=ticket_id)
    return DriveThruTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/preparing",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_preparing(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).mark_preparing(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/ready",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_ready(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).mark_ready(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/call",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def call_up(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).call_up(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/served",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def mark_served(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).mark_served(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.post(
    "/tickets/{ticket_id}/abandon",
    response_model=DriveThruTicketRead,
    dependencies=[Depends(requires(Permission.ORDERS_VOID))],
)
async def abandon_ticket(
    ticket_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DriveThruTicketRead:
    ticket = await QsrService(db).abandon(
        tenant_id=user.tenant_id, ticket_id=ticket_id
    )
    return DriveThruTicketRead.model_validate(ticket)


@router.get(
    "/board",
    response_model=BoardRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def board(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BoardRead:
    tickets = await QsrService(db).list_active(tenant_id=user.tenant_id)
    buckets: dict[DriveThruStatus, list[DriveThruTicketRead]] = {
        DriveThruStatus.ORDERING: [],
        DriveThruStatus.PREPARING: [],
        DriveThruStatus.READY: [],
    }
    for t in tickets:
        buckets[t.status].append(DriveThruTicketRead.model_validate(t))
    return BoardRead(
        ordering=buckets[DriveThruStatus.ORDERING],
        preparing=buckets[DriveThruStatus.PREPARING],
        ready=buckets[DriveThruStatus.READY],
    )
