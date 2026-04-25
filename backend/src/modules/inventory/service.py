from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.inventory.entity import StockMovementKind
from src.modules.inventory.repository import InventoryRepository, LocationRepository


class InventoryService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        inventory: InventoryRepository | None = None,
        locations: LocationRepository | None = None,
    ) -> None:
        self._session = session
        self._inventory = inventory or InventoryRepository(session)
        self._locations = locations or LocationRepository(session)

    async def default_location_id(self, *, tenant_id: UUID) -> UUID:
        location = await self._locations.default_for_tenant(tenant_id)
        return location.id

    async def receive_stock(
        self, *, tenant_id: UUID, product_id: UUID, location_id: UUID, quantity: int
    ) -> int:
        assert quantity > 0, "Use adjust() for negative deltas"
        return await self._inventory.adjust(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            delta=quantity,
            kind=StockMovementKind.RECEIVE,
        )

    async def consume_for_sale(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        location_id: UUID,
        quantity: int,
        order_id: UUID,
    ) -> int:
        return await self._inventory.adjust(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            delta=-quantity,
            kind=StockMovementKind.SALE,
            reference_id=order_id,
        )

    async def current_quantity(
        self, *, tenant_id: UUID, product_id: UUID, location_id: UUID
    ) -> int:
        level = await self._inventory.get_level(
            tenant_id=tenant_id, product_id=product_id, location_id=location_id
        )
        return level.quantity if level else 0

    async def list_levels(
        self, *, tenant_id: UUID, page: int, page_size: int
    ) -> tuple[list[tuple], bool]:  # type: ignore[type-arg]
        offset = max(0, (page - 1) * page_size)
        return await self._inventory.list_levels(
            tenant_id=tenant_id, limit=page_size, offset=offset
        )

    async def list_locations(self, *, tenant_id: UUID):  # type: ignore[no-untyped-def]
        await self._locations.default_for_tenant(tenant_id)
        return await self._locations.list(tenant_id=tenant_id)

    async def create_location(
        self, *, tenant_id: UUID, code: str, name: str
    ):  # type: ignore[no-untyped-def]
        from src.core.errors import ConflictError

        existing = await self._locations.by_code(tenant_id=tenant_id, code=code)
        if existing is not None:
            raise ConflictError("A location with that code already exists.")
        return await self._locations.add(tenant_id=tenant_id, code=code, name=name)

    async def manual_adjust(
        self, *, tenant_id: UUID, product_id: UUID, delta: int
    ) -> int:
        location_id = await self.default_location_id(tenant_id=tenant_id)
        kind = (
            StockMovementKind.RECEIVE if delta > 0 else StockMovementKind.ADJUSTMENT
        )
        return await self._inventory.adjust(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            delta=delta,
            kind=kind,
        )

    async def transfer_stock(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        source_location_id: UUID,
        destination_location_id: UUID,
        quantity: int,
    ) -> tuple[int, int]:
        """Move stock between two locations atomically. Returns (source_qty, dest_qty)."""
        from src.core.errors import ConflictError, ValidationError

        if quantity <= 0:
            raise ValidationError("Transfer quantity must be greater than zero.")
        if source_location_id == destination_location_id:
            raise ValidationError("Source and destination must differ.")

        source_level = await self._inventory.get_level(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=source_location_id,
        )
        on_hand = source_level.quantity if source_level else 0
        if on_hand < quantity:
            raise ConflictError("Source location does not have enough stock.")

        source_qty = await self._inventory.adjust(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=source_location_id,
            delta=-quantity,
            kind=StockMovementKind.TRANSFER_OUT,
        )
        dest_qty = await self._inventory.adjust(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=destination_location_id,
            delta=quantity,
            kind=StockMovementKind.TRANSFER_IN,
        )
        return source_qty, dest_qty

    async def set_reorder_point(
        self, *, tenant_id: UUID, product_id: UUID, reorder_point: int
    ) -> int:
        location_id = await self.default_location_id(tenant_id=tenant_id)
        level = await self._inventory.set_reorder_point(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            reorder_point=reorder_point,
        )
        return level.reorder_point
