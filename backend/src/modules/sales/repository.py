from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.sales.entity import Order, OrderItem, OrderStatus, Payment


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        return order

    async def add_items(self, items: list[OrderItem]) -> None:
        self._session.add_all(items)
        await self._session.flush()

    async def add_payment(self, payment: Payment) -> Payment:
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def get_with_relations(self, *, tenant_id: UUID, order_id: UUID) -> Order | None:
        """Eager-load order + items + payments to avoid N+1 in the read path."""
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.tenant_id == tenant_id)
            .options(selectinload("*"))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_items(self, *, order_id: UUID) -> list[OrderItem]:
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_payments(self, *, order_id: UUID) -> list[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
        status: "OrderStatus | None" = None,
        since: "datetime | None" = None,
        until: "datetime | None" = None,
    ) -> tuple[list[Order], bool]:
        """Cursor-safe pagination: fetch limit+1 to detect has_more.

        Optional filters: status, and an opened-at date range.
        """
        stmt = (
            select(Order)
            .where(Order.tenant_id == tenant_id)
            .order_by(Order.opened_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Order.status == status)
        if since is not None:
            stmt = stmt.where(Order.opened_at >= since)
        if until is not None:
            stmt = stmt.where(Order.opened_at < until)
        stmt = stmt.limit(limit + 1).offset(offset)
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more
