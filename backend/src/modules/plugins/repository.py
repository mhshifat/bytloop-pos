from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.plugins.entity import PluginInstall


class PluginRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(self, *, tenant_id: UUID) -> list[PluginInstall]:
        stmt = (
            select(PluginInstall)
            .where(PluginInstall.tenant_id == tenant_id)
            .order_by(PluginInstall.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get(
        self, *, tenant_id: UUID, code: str
    ) -> PluginInstall | None:
        stmt = select(PluginInstall).where(
            PluginInstall.tenant_id == tenant_id,
            PluginInstall.code == code,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_enabled_global(self) -> list[PluginInstall]:
        """All enabled installs across every tenant — used at app boot to
        re-register handlers. Called exactly once per process startup."""
        stmt = select(PluginInstall).where(PluginInstall.enabled.is_(True))
        return list((await self._session.execute(stmt)).scalars().all())

    async def upsert(
        self,
        *,
        tenant_id: UUID,
        code: str,
        enabled: bool,
        config: dict[str, Any] | None = None,
    ) -> PluginInstall:
        existing = await self.get(tenant_id=tenant_id, code=code)
        if existing is not None:
            existing.enabled = enabled
            if config is not None:
                existing.config = config
            await self._session.flush()
            return existing
        install = PluginInstall(
            tenant_id=tenant_id,
            code=code,
            enabled=enabled,
            config=dict(config or {}),
        )
        self._session.add(install)
        await self._session.flush()
        return install

    async def remove(self, *, tenant_id: UUID, code: str) -> bool:
        existing = await self.get(tenant_id=tenant_id, code=code)
        if existing is None:
            return False
        await self._session.delete(existing)
        await self._session.flush()
        return True
