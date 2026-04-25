from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import DATE
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.verticals.fnb.qsr.entity import DriveThruStatus, DriveThruTicket


class QsrService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _next_call_number(self, *, tenant_id: UUID) -> int:
        """Sequential per tenant per UTC day.

        Rolls over at midnight UTC: the MAX(call_number) query is scoped
        to today's date (UTC), so tomorrow's first ticket is #1 again.
        """
        today_utc = datetime.now(tz=UTC).date()
        stmt = select(func.coalesce(func.max(DriveThruTicket.call_number), 0)).where(
            DriveThruTicket.tenant_id == tenant_id,
            cast(DriveThruTicket.created_at, DATE) == today_utc,
        )
        current = (await self._session.execute(stmt)).scalar_one()
        return int(current) + 1

    async def create_ticket(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        lane: str | None = None,
        estimated_ready_at: datetime | None = None,
    ) -> DriveThruTicket:
        call_number = await self._next_call_number(tenant_id=tenant_id)
        ticket = DriveThruTicket(
            tenant_id=tenant_id,
            order_id=order_id,
            call_number=call_number,
            status=DriveThruStatus.ORDERING,
            lane=lane,
            estimated_ready_at=estimated_ready_at,
            called_at=None,
            served_at=None,
        )
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def get(self, *, tenant_id: UUID, ticket_id: UUID) -> DriveThruTicket:
        ticket = await self._session.get(DriveThruTicket, ticket_id)
        if ticket is None or ticket.tenant_id != tenant_id:
            raise NotFoundError("Ticket not found.")
        return ticket

    async def list_active(self, *, tenant_id: UUID) -> list[DriveThruTicket]:
        stmt = (
            select(DriveThruTicket)
            .where(
                DriveThruTicket.tenant_id == tenant_id,
                DriveThruTicket.status.in_(
                    [
                        DriveThruStatus.ORDERING,
                        DriveThruStatus.PREPARING,
                        DriveThruStatus.READY,
                    ]
                ),
            )
            .order_by(DriveThruTicket.call_number)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def mark_preparing(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> DriveThruTicket:
        ticket = await self.get(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.status = DriveThruStatus.PREPARING
        await self._session.flush()
        return ticket

    async def mark_ready(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> DriveThruTicket:
        ticket = await self.get(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.status = DriveThruStatus.READY
        await self._session.flush()
        return ticket

    async def call_up(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> DriveThruTicket:
        ticket = await self.get(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.called_at = datetime.now(tz=UTC)
        await self._session.flush()
        return ticket

    async def mark_served(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> DriveThruTicket:
        ticket = await self.get(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.status = DriveThruStatus.SERVED
        ticket.served_at = datetime.now(tz=UTC)
        await self._session.flush()
        return ticket

    async def abandon(
        self, *, tenant_id: UUID, ticket_id: UUID
    ) -> DriveThruTicket:
        ticket = await self.get(tenant_id=tenant_id, ticket_id=ticket_id)
        ticket.status = DriveThruStatus.ABANDONED
        await self._session.flush()
        return ticket
