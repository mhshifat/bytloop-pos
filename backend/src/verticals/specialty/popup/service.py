from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.modules.catalog.api import Product
from src.modules.inventory.api import InventoryService
from src.verticals.specialty.popup.entity import (
    PopupEvent,
    PopupInventorySnapshot,
    PopupStall,
)


@dataclass(slots=True)
class SoldLine:
    product_id: UUID
    opening_stock: int
    closing_stock: int
    sold_count: int


class PopupService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._inventory = InventoryService(session)

    # ──────────────────────────────────────────────
    # Events
    # ──────────────────────────────────────────────

    async def list_events(self, *, tenant_id: UUID) -> list[PopupEvent]:
        stmt = (
            select(PopupEvent)
            .where(PopupEvent.tenant_id == tenant_id)
            .order_by(PopupEvent.starts_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_event(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        venue: str,
        starts_at: datetime,
        ends_at: datetime,
        location_notes: str | None = None,
    ) -> PopupEvent:
        if ends_at <= starts_at:
            raise ConflictError("Event must end after it starts.")
        existing_stmt = select(PopupEvent).where(
            PopupEvent.tenant_id == tenant_id, PopupEvent.code == code
        )
        if (await self._session.execute(existing_stmt)).scalar_one_or_none() is not None:
            raise ConflictError("An event with that code already exists.")
        event = PopupEvent(
            tenant_id=tenant_id,
            code=code,
            name=name,
            venue=venue,
            starts_at=starts_at,
            ends_at=ends_at,
            location_notes=location_notes,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def _get_event(self, *, tenant_id: UUID, event_id: UUID) -> PopupEvent:
        event = await self._session.get(PopupEvent, event_id)
        if event is None or event.tenant_id != tenant_id:
            raise NotFoundError("Event not found.")
        return event

    # ──────────────────────────────────────────────
    # Stalls
    # ──────────────────────────────────────────────

    async def create_stall(
        self,
        *,
        tenant_id: UUID,
        event_id: UUID,
        stall_label: str,
        operator_user_id: UUID | None = None,
    ) -> PopupStall:
        await self._get_event(tenant_id=tenant_id, event_id=event_id)
        stall = PopupStall(
            tenant_id=tenant_id,
            event_id=event_id,
            stall_label=stall_label,
            operator_user_id=operator_user_id,
        )
        self._session.add(stall)
        await self._session.flush()
        return stall

    async def list_stalls(
        self, *, tenant_id: UUID, event_id: UUID
    ) -> list[PopupStall]:
        stmt = (
            select(PopupStall)
            .where(
                PopupStall.tenant_id == tenant_id,
                PopupStall.event_id == event_id,
            )
            .order_by(PopupStall.stall_label)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Open / close
    # ──────────────────────────────────────────────

    async def open_event(
        self, *, tenant_id: UUID, event_id: UUID
    ) -> list[PopupInventorySnapshot]:
        """Snapshot opening_stock for every tracked product at the tenant's default location."""
        event = await self._get_event(tenant_id=tenant_id, event_id=event_id)

        # Refuse to re-open if snapshots already exist; opening_stock is the
        # "before" line of the delta and must be pristine.
        existing_stmt = select(PopupInventorySnapshot).where(
            PopupInventorySnapshot.tenant_id == tenant_id,
            PopupInventorySnapshot.event_id == event.id,
        )
        if (await self._session.execute(existing_stmt)).scalars().first() is not None:
            raise ConflictError("Event has already been opened.")

        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)

        product_stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.track_inventory.is_(True),
        )
        products = list(
            (await self._session.execute(product_stmt)).scalars().all()
        )

        snapshots: list[PopupInventorySnapshot] = []
        for product in products:
            qty = await self._inventory.current_quantity(
                tenant_id=tenant_id,
                product_id=product.id,
                location_id=location_id,
            )
            snap = PopupInventorySnapshot(
                tenant_id=tenant_id,
                event_id=event.id,
                product_id=product.id,
                opening_stock=qty,
                closing_stock=None,
                closed_at=None,
            )
            self._session.add(snap)
            snapshots.append(snap)
        await self._session.flush()
        return snapshots

    async def close_event(
        self, *, tenant_id: UUID, event_id: UUID
    ) -> list[SoldLine]:
        """Write closing_stock to each snapshot and return a delta report."""
        event = await self._get_event(tenant_id=tenant_id, event_id=event_id)
        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)

        stmt = select(PopupInventorySnapshot).where(
            PopupInventorySnapshot.tenant_id == tenant_id,
            PopupInventorySnapshot.event_id == event.id,
        )
        snapshots = list((await self._session.execute(stmt)).scalars().all())
        if not snapshots:
            raise ConflictError(
                "Event was never opened — nothing to close."
            )
        if all(s.closing_stock is not None for s in snapshots):
            raise ConflictError("Event is already closed.")

        now = datetime.now(tz=UTC)
        report: list[SoldLine] = []
        for snap in snapshots:
            closing = await self._inventory.current_quantity(
                tenant_id=tenant_id,
                product_id=snap.product_id,
                location_id=location_id,
            )
            snap.closing_stock = closing
            snap.closed_at = now
            report.append(
                SoldLine(
                    product_id=snap.product_id,
                    opening_stock=snap.opening_stock,
                    closing_stock=closing,
                    sold_count=max(0, snap.opening_stock - closing),
                )
            )
        await self._session.flush()
        return report
