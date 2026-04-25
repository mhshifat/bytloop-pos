from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from src.core.errors import NotFoundError
from src.core.realtime import publish
from src.modules.inventory.api import InventoryService
from src.verticals.fnb.restaurant.entity import (
    KdsStation,
    KotItem,
    KotStatus,
    KotTicket,
    ProductStationRoute,
    RestaurantTable,
    TableStatus,
)
from src.verticals.fnb.restaurant.schemas import KotItemInput, TableCreate


class RestaurantService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        inventory: InventoryService | None = None,
    ) -> None:
        self._session = session
        self._inventory = inventory or InventoryService(session)

    # ──────────────────────────────────────────────
    # Tables
    # ──────────────────────────────────────────────

    async def list_tables(self, *, tenant_id: UUID) -> list[RestaurantTable]:
        stmt = (
            select(RestaurantTable)
            .where(RestaurantTable.tenant_id == tenant_id)
            .order_by(RestaurantTable.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_table(self, *, tenant_id: UUID, data: TableCreate) -> RestaurantTable:
        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)
        table = RestaurantTable(
            tenant_id=tenant_id,
            location_id=location_id,
            code=data.code,
            label=data.label,
            seats=data.seats,
            status=TableStatus.AVAILABLE,
            current_order_id=None,
        )
        self._session.add(table)
        await self._session.flush()
        return table

    # ──────────────────────────────────────────────
    # KOT / KDS
    # ──────────────────────────────────────────────

    async def fire_kot(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        station: KdsStation,
        items: list[KotItemInput],
        course: int = 1,
    ) -> KotTicket:
        ticket = KotTicket(
            tenant_id=tenant_id,
            order_id=order_id,
            station=station,
            status=KotStatus.NEW,
            number=f"K-{str(ULID())[-6:]}",
            course=course,
            ready_at=None,
        )
        self._session.add(ticket)
        await self._session.flush()

        self._session.add_all(
            [
                KotItem(
                    tenant_id=tenant_id,
                    ticket_id=ticket.id,
                    product_id=i.product_id,
                    name_snapshot=i.name_snapshot,
                    quantity=i.quantity,
                    modifier_notes=i.modifier_notes,
                )
                for i in items
            ]
        )
        await self._session.flush()
        await publish(
            tenant_id,
            f"kds:{station.value}",
            {"id": str(ticket.id), "event": "fired", "course": course},
        )
        return ticket

    async def fire_order(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        items: list[KotItemInput],
    ) -> list[KotTicket]:
        """Auto-route each line to its configured station+course and fire.

        One ticket per (station, course) combo so the kitchen gets a
        coherent ticket — instead of one monster ticket with mixed courses.
        """
        # Build routing map in one query
        product_ids = [i.product_id for i in items]
        routes: dict[UUID, tuple[KdsStation, int]] = {}
        if product_ids:
            stmt = select(ProductStationRoute).where(
                ProductStationRoute.tenant_id == tenant_id,
                ProductStationRoute.product_id.in_(product_ids),
            )
            for route in (await self._session.execute(stmt)).scalars().all():
                routes[route.product_id] = (route.station, route.course)

        # Group by (station, course)
        buckets: dict[tuple[KdsStation, int], list[KotItemInput]] = {}
        for item in items:
            station, course = routes.get(item.product_id, (KdsStation.KITCHEN, 1))
            buckets.setdefault((station, course), []).append(item)

        tickets: list[KotTicket] = []
        for (station, course), bucket_items in buckets.items():
            ticket = await self.fire_kot(
                tenant_id=tenant_id,
                order_id=order_id,
                station=station,
                items=bucket_items,
                course=course,
            )
            tickets.append(ticket)
        return tickets

    async def upsert_route(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        station: KdsStation,
        course: int,
    ) -> ProductStationRoute:
        stmt = select(ProductStationRoute).where(
            ProductStationRoute.tenant_id == tenant_id,
            ProductStationRoute.product_id == product_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.station = station
            existing.course = course
            await self._session.flush()
            return existing
        route = ProductStationRoute(
            tenant_id=tenant_id,
            product_id=product_id,
            station=station,
            course=course,
        )
        self._session.add(route)
        await self._session.flush()
        return route

    async def list_routes(self, *, tenant_id: UUID) -> list[ProductStationRoute]:
        stmt = select(ProductStationRoute).where(
            ProductStationRoute.tenant_id == tenant_id
        )
        return list((await self._session.execute(stmt)).scalars().all())

    @staticmethod
    def calculate_service_charge(
        subtotal_cents: int, *, service_charge_pct: float = 10.0
    ) -> int:
        """Default 10% — tenant config can override via tenant.config.
        Rounded to the nearest cent using banker's rounding for consistency.
        """
        if subtotal_cents <= 0 or service_charge_pct <= 0:
            return 0
        return int(round(subtotal_cents * (service_charge_pct / 100)))

    async def list_station_tickets(
        self, *, tenant_id: UUID, station: KdsStation
    ) -> list[KotTicket]:
        stmt = (
            select(KotTicket)
            .where(
                KotTicket.tenant_id == tenant_id,
                KotTicket.station == station,
                KotTicket.status.in_(
                    [KotStatus.NEW, KotStatus.PREPARING, KotStatus.READY]
                ),
            )
            .order_by(KotTicket.fired_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def update_kot_status(
        self, *, tenant_id: UUID, ticket_id: UUID, status: KotStatus
    ) -> KotTicket:
        ticket = await self._session.get(KotTicket, ticket_id)
        if ticket is None or ticket.tenant_id != tenant_id:
            raise NotFoundError("Ticket not found.")
        ticket.status = status
        if status == KotStatus.READY:
            ticket.ready_at = datetime.now(tz=UTC)
        await self._session.flush()
        await publish(
            ticket.tenant_id,
            f"kds:{ticket.station.value}",
            {"id": str(ticket.id), "event": "status", "status": status.value},
        )
        return ticket
