from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.modules.plugins.entity import PluginInstall
from src.modules.plugins.registry import (
    PluginMeta,
    available_plugins,
    get_plugin,
)
from src.modules.plugins.repository import PluginRepository


class PluginService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PluginRepository(session)

    def available(self) -> list[PluginMeta]:
        return available_plugins()

    async def installed(self, *, tenant_id: UUID) -> list[PluginInstall]:
        return await self._repo.list_for_tenant(tenant_id=tenant_id)

    async def install(
        self,
        *,
        tenant_id: UUID,
        code: str,
        enabled: bool = True,
        config: dict[str, Any] | None = None,
    ) -> PluginInstall:
        plugin = get_plugin(code)
        if plugin is None:
            raise NotFoundError(f"Unknown plugin: {code}")
        install = await self._repo.upsert(
            tenant_id=tenant_id, code=code, enabled=enabled, config=config
        )
        # Unsubscribe first so re-enabling doesn't double-register on top
        # of any prior registration from this process.
        plugin.unregister(tenant_id)
        if enabled:
            plugin.register(tenant_id, dict(install.config or {}))
        return install

    async def uninstall(self, *, tenant_id: UUID, code: str) -> None:
        plugin = get_plugin(code)
        if plugin is not None:
            plugin.unregister(tenant_id)
        removed = await self._repo.remove(tenant_id=tenant_id, code=code)
        if not removed:
            raise NotFoundError("Plugin is not installed.")

    async def set_enabled(
        self, *, tenant_id: UUID, code: str, enabled: bool
    ) -> PluginInstall:
        existing = await self._repo.get(tenant_id=tenant_id, code=code)
        if existing is None:
            raise NotFoundError("Plugin is not installed.")
        return await self.install(
            tenant_id=tenant_id,
            code=code,
            enabled=enabled,
            config=dict(existing.config or {}),
        )

    async def bootstrap_all(self) -> int:
        """Re-register every enabled install at process start.

        The event-bus subscriber list is in-memory so a restart wipes it.
        Called once from the FastAPI lifespan — returns the count registered
        for logs + readiness.
        """
        count = 0
        for install in await self._repo.list_enabled_global():
            plugin = get_plugin(install.code)
            if plugin is None:
                # Plugin code was removed from this build — skip silently;
                # uninstalling from the UI is the operator's call.
                continue
            plugin.register(install.tenant_id, dict(install.config or {}))
            count += 1
        return count
