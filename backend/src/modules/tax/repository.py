from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tax.entity import TaxRule


class TaxRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, *, tenant_id: UUID) -> list[TaxRule]:
        stmt = (
            select(TaxRule)
            .where(TaxRule.tenant_id == tenant_id, TaxRule.is_active.is_(True))
            .order_by(TaxRule.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, rule: TaxRule) -> TaxRule:
        self._session.add(rule)
        await self._session.flush()
        return rule
