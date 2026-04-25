from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.discounts.entity import Discount


class DiscountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_code(self, *, tenant_id: UUID, code: str) -> Discount | None:
        stmt = select(Discount).where(
            Discount.tenant_id == tenant_id,
            Discount.code == code.upper(),
            Discount.is_active.is_(True),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_active(self, *, tenant_id: UUID) -> list[Discount]:
        stmt = (
            select(Discount)
            .where(Discount.tenant_id == tenant_id, Discount.is_active.is_(True))
            .order_by(Discount.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, discount: Discount) -> Discount:
        self._session.add(discount)
        await self._session.flush()
        return discount
