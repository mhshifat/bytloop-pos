from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.services.laundry.entity import (
    LaundryItem,
    LaundryStatus,
    LaundryTicket,
)


class LaundryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Tickets
    # ──────────────────────────────────────────────

    async def create_ticket(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        ticket_no: str,
        item_count: int,
        promised_at: datetime | None = None,
    ) -> LaundryTicket:
        # Enforce per-tenant uniqueness of the human-facing ticket number up
        # front so we produce a friendly ConflictError instead of an IntegrityError.
        exists_stmt = select(LaundryTicket).where(
            LaundryTicket.tenant_id == tenant_id,
            LaundryTicket.ticket_no == ticket_no,
        )
        if (await self._session.execute(exists_stmt)).scalar_one_or_none() is not None:
            raise ConflictError("That ticket number is already in use.")

        ticket = LaundryTicket(
            tenant_id=tenant_id,
            customer_id=customer_id,
            ticket_no=ticket_no,
            item_count=item_count,
            status=LaundryStatus.RECEIVED,
            promised_at=promised_at,
        )
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def list_tickets(
        self, *, tenant_id: UUID, status: LaundryStatus | None = None
    ) -> list[LaundryTicket]:
        stmt = select(LaundryTicket).where(LaundryTicket.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(LaundryTicket.status == status)
        stmt = stmt.order_by(LaundryTicket.dropped_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_ticket(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> LaundryTicket:
        ticket = await self._session.get(LaundryTicket, ticket_id)
        if ticket is None or ticket.tenant_id != tenant_id:
            raise NotFoundError("Ticket not found.")
        return ticket

    # ──────────────────────────────────────────────
    # Items
    # ──────────────────────────────────────────────

    async def add_items(
        self,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
        items: list[dict],
    ) -> list[LaundryItem]:
        ticket = await self.get_ticket(tenant_id=tenant_id, ticket_id=ticket_id)
        created: list[LaundryItem] = []
        for row in items:
            item = LaundryItem(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                description=row["description"],
                quantity=int(row.get("quantity", 1)),
                service_type=row.get("service_type", ""),
                price_cents=int(row.get("price_cents", 0)),
            )
            self._session.add(item)
            created.append(item)
        ticket.item_count += sum(int(r.get("quantity", 1)) for r in items)
        await self._session.flush()
        return created

    async def list_items(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> list[LaundryItem]:
        stmt = select(LaundryItem).where(
            LaundryItem.tenant_id == tenant_id,
            LaundryItem.ticket_id == ticket_id,
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Status transitions
    # ──────────────────────────────────────────────

    async def mark_ready(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> LaundryTicket:
        ticket = await self.get_ticket(tenant_id=tenant_id, ticket_id=ticket_id)
        if ticket.status == LaundryStatus.COLLECTED:
            raise ConflictError("Ticket has already been collected.")
        if ticket.status == LaundryStatus.LOST:
            raise ConflictError("Ticket is marked as lost.")
        ticket.status = LaundryStatus.READY
        await self._session.flush()
        return ticket

    async def mark_collected(
        self,
        *,
        tenant_id: UUID,
        ticket_id: UUID,
        order_id: UUID | None,
    ) -> LaundryTicket:
        ticket = await self.get_ticket(tenant_id=tenant_id, ticket_id=ticket_id)
        if ticket.status == LaundryStatus.COLLECTED:
            raise ConflictError("Ticket has already been collected.")
        if ticket.status == LaundryStatus.LOST:
            raise ConflictError("Ticket is marked as lost.")
        ticket.status = LaundryStatus.COLLECTED
        ticket.collected_at = datetime.now(tz=UTC)
        ticket.order_id = order_id
        await self._session.flush()
        return ticket

    async def update_status(
        self, *, tenant_id: UUID, ticket_id: UUID, status: LaundryStatus
    ) -> LaundryTicket:
        ticket = await self.get_ticket(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.status = status
        if status == LaundryStatus.COLLECTED and ticket.collected_at is None:
            ticket.collected_at = datetime.now(tz=UTC)
        await self._session.flush()
        return ticket
