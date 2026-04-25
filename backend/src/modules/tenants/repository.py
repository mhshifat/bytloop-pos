from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tenants.entity import Tenant


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        return await self._session.get(Tenant, tenant_id)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(select(Tenant).where(Tenant.slug == slug.lower()))
        return result.scalar_one_or_none()

    async def create(self, *, slug: str, name: str, country: str, default_currency: str) -> Tenant:
        tenant = Tenant(
            slug=slug.lower(),
            name=name,
            country=country.upper(),
            default_currency=default_currency.upper(),
            config={},
        )
        self._session.add(tenant)
        await self._session.flush()
        return tenant
