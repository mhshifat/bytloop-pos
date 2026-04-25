from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.entity import (
    InventoryLevel,
    Location,
    StockMovement,
    StockMovementKind,
)


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def default_for_tenant(self, tenant_id: UUID) -> Location:
        stmt = (
            select(Location)
            .where(Location.tenant_id == tenant_id)
            .order_by(Location.created_at)
            .limit(1)
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing
        loc = Location(tenant_id=tenant_id, code="main", name="Main")
        self._session.add(loc)
        await self._session.flush()
        return loc

    async def list(self, *, tenant_id: UUID) -> list[Location]:
        stmt = (
            select(Location).where(Location.tenant_id == tenant_id).order_by(Location.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def by_code(self, *, tenant_id: UUID, code: str) -> Location | None:
        stmt = select(Location).where(
            Location.tenant_id == tenant_id, Location.code == code.lower()
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, *, tenant_id: UUID, code: str, name: str) -> Location:
        loc = Location(tenant_id=tenant_id, code=code.lower(), name=name)
        self._session.add(loc)
        await self._session.flush()
        return loc


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_level(
        self, *, tenant_id: UUID, product_id: UUID, location_id: UUID
    ) -> InventoryLevel | None:
        stmt = select(InventoryLevel).where(
            InventoryLevel.tenant_id == tenant_id,
            InventoryLevel.product_id == product_id,
            InventoryLevel.location_id == location_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_levels(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[InventoryLevel, str, str, str, str]], bool]:
        """Returns (level, product_name, product_sku, location_code, location_name), has_more.

        Joins through the public ``catalog.api.Product`` (not catalog.entity
        directly) to respect the module boundary contract.
        """
        from src.modules.catalog.api import Product

        stmt = (
            select(
                InventoryLevel,
                Product.name,
                Product.sku,
                Location.code,
                Location.name,
            )
            .join(Product, Product.id == InventoryLevel.product_id)
            .join(Location, Location.id == InventoryLevel.location_id)
            .where(InventoryLevel.tenant_id == tenant_id)
            .order_by(InventoryLevel.quantity.asc(), Product.name)
            .limit(limit + 1)
            .offset(offset)
        )
        rows = [
            (lvl, name, sku, loc_code, loc_name)
            for lvl, name, sku, loc_code, loc_name in (
                await self._session.execute(stmt)
            ).all()
        ]
        has_more = len(rows) > limit
        return rows[:limit], has_more

    async def set_reorder_point(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        location_id: UUID,
        reorder_point: int,
    ) -> InventoryLevel:
        level = await self.get_level(
            tenant_id=tenant_id, product_id=product_id, location_id=location_id
        )
        if level is None:
            level = InventoryLevel(
                tenant_id=tenant_id,
                product_id=product_id,
                location_id=location_id,
                quantity=0,
                reorder_point=reorder_point,
            )
            self._session.add(level)
        else:
            level.reorder_point = reorder_point
        await self._session.flush()
        return level

    async def adjust(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        location_id: UUID,
        delta: int,
        kind: StockMovementKind,
        reference_id: UUID | None = None,
    ) -> int:
        """Apply a delta and record a ledger row. Returns the new balance."""
        level = await self.get_level(
            tenant_id=tenant_id, product_id=product_id, location_id=location_id
        )
        if level is None:
            level = InventoryLevel(
                tenant_id=tenant_id,
                product_id=product_id,
                location_id=location_id,
                quantity=0,
                reorder_point=0,
            )
            self._session.add(level)
        level.quantity += delta

        movement = StockMovement(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            kind=kind,
            quantity_delta=delta,
            reference_id=reference_id,
        )
        self._session.add(movement)
        await self._session.flush()
        return level.quantity
