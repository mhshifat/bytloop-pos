from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.plugins.schemas import (
    PluginInstallRead,
    PluginInstallRequest,
    PluginMetaRead,
    PluginToggleRequest,
)
from src.modules.plugins.service import PluginService

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/available", response_model=list[PluginMetaRead])
async def list_available(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PluginMetaRead]:
    metas = PluginService(db).available()
    return [
        PluginMetaRead(
            code=m.code,
            name=m.name,
            description=m.description,
            version=m.version,
            hooks=list(m.hooks),
        )
        for m in metas
    ]


@router.get("/installed", response_model=list[PluginInstallRead])
async def list_installed(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PluginInstallRead]:
    rows = await PluginService(db).installed(tenant_id=user.tenant_id)
    return [PluginInstallRead.model_validate(r) for r in rows]


@router.post(
    "/install",
    response_model=PluginInstallRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def install_plugin(
    data: PluginInstallRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PluginInstallRead:
    install = await PluginService(db).install(
        tenant_id=user.tenant_id,
        code=data.code,
        enabled=data.enabled,
        config=data.config,
    )
    return PluginInstallRead.model_validate(install)


@router.patch(
    "/{code}",
    response_model=PluginInstallRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def toggle_plugin(
    code: str,
    data: PluginToggleRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PluginInstallRead:
    install = await PluginService(db).set_enabled(
        tenant_id=user.tenant_id, code=code, enabled=data.enabled
    )
    return PluginInstallRead.model_validate(install)


@router.delete(
    "/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def uninstall_plugin(
    code: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> None:
    await PluginService(db).uninstall(tenant_id=user.tenant_id, code=code)
