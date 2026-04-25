from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.specialty.tickets.entity import (
    EventInstance,
    EventStatus,
    IssuedTicket,
    TicketStatus,
    TicketType,
)


class TicketsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Events
    # ──────────────────────────────────────────────

    async def list_events(self, *, tenant_id: UUID) -> list[EventInstance]:
        stmt = (
            select(EventInstance)
            .where(EventInstance.tenant_id == tenant_id)
            .order_by(EventInstance.starts_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_event(
        self,
        *,
        tenant_id: UUID,
        title: str,
        starts_at: datetime,
        ends_at: datetime,
        venue: str,
    ) -> EventInstance:
        if ends_at <= starts_at:
            raise ValidationError("Event end must be after its start.")
        event = EventInstance(
            tenant_id=tenant_id,
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            venue=venue,
            status=EventStatus.ACTIVE,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def cancel_event(self, *, tenant_id: UUID, event_id: UUID) -> EventInstance:
        event = await self._session.get(EventInstance, event_id)
        if event is None or event.tenant_id != tenant_id:
            raise NotFoundError("Event not found.")
        event.status = EventStatus.CANCELLED
        await self._session.flush()
        return event

    # ──────────────────────────────────────────────
    # Ticket types
    # ──────────────────────────────────────────────

    async def list_ticket_types(
        self, *, tenant_id: UUID, event_id: UUID
    ) -> list[TicketType]:
        stmt = (
            select(TicketType)
            .where(
                TicketType.tenant_id == tenant_id,
                TicketType.event_id == event_id,
            )
            .order_by(TicketType.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add_ticket_type(
        self,
        *,
        tenant_id: UUID,
        event_id: UUID,
        code: str,
        name: str,
        price_cents: int,
        quota: int,
    ) -> TicketType:
        event = await self._session.get(EventInstance, event_id)
        if event is None or event.tenant_id != tenant_id:
            raise NotFoundError("Event not found.")
        ticket_type = TicketType(
            tenant_id=tenant_id,
            event_id=event_id,
            code=code,
            name=name,
            price_cents=price_cents,
            quota=quota,
            sold_count=0,
        )
        self._session.add(ticket_type)
        await self._session.flush()
        return ticket_type

    # ──────────────────────────────────────────────
    # Purchase / scan / void
    # ──────────────────────────────────────────────

    async def purchase_tickets(
        self,
        *,
        tenant_id: UUID,
        ticket_type_id: UUID,
        quantity: int,
        order_id: UUID | None = None,
        holder_names: list[str] | None = None,
    ) -> list[IssuedTicket]:
        if quantity <= 0:
            raise ValidationError("Quantity must be at least 1.")

        ticket_type = await self._session.get(TicketType, ticket_type_id)
        if ticket_type is None or ticket_type.tenant_id != tenant_id:
            raise NotFoundError("Ticket type not found.")

        event = await self._session.get(EventInstance, ticket_type.event_id)
        if event is None or event.status != EventStatus.ACTIVE:
            raise ConflictError("Event is not available for sale.")

        remaining = ticket_type.quota - ticket_type.sold_count
        if remaining < quantity:
            raise ConflictError(
                f"Not enough tickets remaining: asked {quantity}, have {remaining}."
            )

        holders = list(holder_names or [])
        # Pad / trim so we always have exactly `quantity` names.
        while len(holders) < quantity:
            holders.append("")
        holders = holders[:quantity]

        issued: list[IssuedTicket] = []
        for name in holders:
            ticket = IssuedTicket(
                tenant_id=tenant_id,
                ticket_type_id=ticket_type_id,
                order_id=order_id,
                holder_name=name,
                serial_no=f"TKT-{uuid4().hex[:12].upper()}",
                status=TicketStatus.ISSUED,
                scanned_at=None,
            )
            self._session.add(ticket)
            issued.append(ticket)

        ticket_type.sold_count += quantity
        await self._session.flush()
        return issued

    async def _get_ticket_by_serial(
        self, *, tenant_id: UUID, serial_no: str
    ) -> IssuedTicket:
        stmt = select(IssuedTicket).where(
            IssuedTicket.tenant_id == tenant_id,
            IssuedTicket.serial_no == serial_no,
        )
        ticket = (await self._session.execute(stmt)).scalar_one_or_none()
        if ticket is None:
            raise NotFoundError("Ticket not found.")
        return ticket

    async def scan(self, *, tenant_id: UUID, serial_no: str) -> IssuedTicket:
        ticket = await self._get_ticket_by_serial(
            tenant_id=tenant_id, serial_no=serial_no
        )
        if ticket.status == TicketStatus.SCANNED:
            raise ConflictError("Ticket has already been scanned.")
        if ticket.status == TicketStatus.VOIDED:
            raise ConflictError("Ticket is voided.")
        ticket.status = TicketStatus.SCANNED
        ticket.scanned_at = datetime.now(tz=UTC)
        await self._session.flush()
        return ticket

    async def void(self, *, tenant_id: UUID, serial_no: str) -> IssuedTicket:
        ticket = await self._get_ticket_by_serial(
            tenant_id=tenant_id, serial_no=serial_no
        )
        if ticket.status == TicketStatus.SCANNED:
            raise ConflictError("Cannot void a ticket that has already been scanned.")
        ticket.status = TicketStatus.VOIDED
        await self._session.flush()
        return ticket

    async def list_issued(
        self, *, tenant_id: UUID, ticket_type_id: UUID
    ) -> list[IssuedTicket]:
        stmt = (
            select(IssuedTicket)
            .where(
                IssuedTicket.tenant_id == tenant_id,
                IssuedTicket.ticket_type_id == ticket_type_id,
            )
            .order_by(IssuedTicket.issued_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
