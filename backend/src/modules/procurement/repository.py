from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.procurement.entity import (
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, tenant_id: UUID) -> list[Supplier]:
        stmt = select(Supplier).where(Supplier.tenant_id == tenant_id).order_by(Supplier.name)
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, supplier: Supplier) -> Supplier:
        self._session.add(supplier)
        await self._session.flush()
        return supplier


class PurchaseOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, *, tenant_id: UUID, limit: int, offset: int
    ) -> tuple[list[PurchaseOrder], bool]:
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.tenant_id == tenant_id)
            .order_by(PurchaseOrder.created_at.desc())
            .limit(limit + 1)
            .offset(offset)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more

    async def get(
        self, *, tenant_id: UUID, purchase_order_id: UUID
    ) -> PurchaseOrder | None:
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == tenant_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, po: PurchaseOrder) -> PurchaseOrder:
        self._session.add(po)
        await self._session.flush()
        return po

    async def add_items(self, items: list[PurchaseOrderItem]) -> None:
        self._session.add_all(items)
        await self._session.flush()

    async def list_items(self, *, purchase_order_id: UUID) -> list[PurchaseOrderItem]:
        stmt = select(PurchaseOrderItem).where(
            PurchaseOrderItem.purchase_order_id == purchase_order_id
        )
        return list((await self._session.execute(stmt)).scalars().all())
