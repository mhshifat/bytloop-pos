from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.modules.discounts.entity import Discount, DiscountHelpers
from src.modules.discounts.repository import DiscountRepository
from src.modules.discounts.schemas import DiscountCreate


class DiscountService:
    def __init__(self, session: AsyncSession, repo: DiscountRepository | None = None) -> None:
        self._session = session
        self._repo = repo or DiscountRepository(session)

    async def list_active(self, *, tenant_id: UUID) -> list[Discount]:
        return await self._repo.list_active(tenant_id=tenant_id)

    async def create(self, *, tenant_id: UUID, data: DiscountCreate) -> Discount:
        return await self._repo.add(
            Discount(
                tenant_id=tenant_id,
                code=data.code.upper(),
                name=data.name,
                kind=data.kind,
                percent=data.percent,
                amount_cents=data.amount_cents,
                currency=data.currency.upper(),
                is_active=True,
                starts_at=data.starts_at,
                ends_at=data.ends_at,
            )
        )

    async def resolve(self, *, tenant_id: UUID, code: str, subtotal_cents: int) -> int:
        discount = await self._repo.by_code(tenant_id=tenant_id, code=code)
        if discount is None:
            raise NotFoundError("That discount code doesn't apply.")
        return DiscountHelpers.apply(discount, subtotal_cents)
