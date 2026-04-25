from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.customers.entity import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        tenant_id: UUID,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Customer], bool]:
        stmt = (
            select(Customer)
            .where(Customer.tenant_id == tenant_id)
            .order_by(Customer.first_name, Customer.last_name)
        )
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Customer.first_name).like(like),
                    func.lower(Customer.last_name).like(like),
                    func.lower(Customer.email).like(like),
                    Customer.phone.like(like),
                )
            )
        stmt = stmt.limit(limit + 1).offset(offset)
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more

    async def get(self, *, tenant_id: UUID, customer_id: UUID) -> Customer | None:
        stmt = select(Customer).where(
            Customer.id == customer_id, Customer.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, customer: Customer) -> Customer:
        self._session.add(customer)
        await self._session.flush()
        return customer

    async def delete(self, customer: Customer) -> None:
        await self._session.delete(customer)
        await self._session.flush()
