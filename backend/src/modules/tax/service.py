from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tax.entity import TaxRule
from src.modules.tax.repository import TaxRuleRepository
from src.modules.tax.schemas import TaxRuleCreate


class TaxService:
    def __init__(self, session: AsyncSession, repo: TaxRuleRepository | None = None) -> None:
        self._session = session
        self._repo = repo or TaxRuleRepository(session)

    async def list_active(self, *, tenant_id: UUID) -> list[TaxRule]:
        return await self._repo.list_active(tenant_id=tenant_id)

    async def create(self, *, tenant_id: UUID, data: TaxRuleCreate) -> TaxRule:
        return await self._repo.add(
            TaxRule(
                tenant_id=tenant_id,
                code=data.code.upper(),
                name=data.name,
                rate=data.rate,
                is_inclusive=data.is_inclusive,
                is_active=True,
            )
        )
