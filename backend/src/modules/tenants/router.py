from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import NotFoundError
from src.core.permissions import Permission
from src.modules.tenants.repository import TenantRepository
from src.modules.tenants.schemas import (
    TenantBrandRead,
    TenantBrandUpdate,
    TenantRead,
    TenantUpdate,
)

router = APIRouter(prefix="/tenant", tags=["tenant"])


@router.get("", response_model=TenantRead)
async def get_current_tenant(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TenantRead:
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found.")
    return TenantRead.model_validate(tenant)


@router.patch(
    "",
    response_model=TenantRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def update_current_tenant(
    data: TenantUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TenantRead:
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found.")
    if data.name is not None:
        tenant.name = data.name
    if data.country is not None:
        tenant.country = data.country.upper()
    if data.default_currency is not None:
        tenant.default_currency = data.default_currency.upper()
    if data.vertical_profile is not None:
        # Reject unknown profiles rather than silently storing garbage.
        from src.modules.tenants.entity import VerticalProfile

        try:
            tenant.vertical_profile = VerticalProfile(data.vertical_profile)
        except ValueError as exc:
            raise NotFoundError(f"Unknown vertical profile: {data.vertical_profile}") from exc
    await db.flush()
    return TenantRead.model_validate(tenant)


def _brand_from_config(config: dict) -> TenantBrandRead:  # type: ignore[type-arg]
    brand = config.get("brand") if isinstance(config, dict) else None
    if not isinstance(brand, dict):
        return TenantBrandRead()
    return TenantBrandRead(
        logo_url=brand.get("logoUrl") or brand.get("logo_url"),
        primary_color=brand.get("primaryColor") or brand.get("primary_color"),
        accent_color=brand.get("accentColor") or brand.get("accent_color"),
        receipt_header=brand.get("receiptHeader") or brand.get("receipt_header"),
        receipt_footer=brand.get("receiptFooter") or brand.get("receipt_footer"),
    )


@router.get("/brand", response_model=TenantBrandRead)
async def get_brand(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TenantBrandRead:
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found.")
    return _brand_from_config(tenant.config or {})


@router.put(
    "/brand",
    response_model=TenantBrandRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def update_brand(
    data: TenantBrandUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TenantBrandRead:
    """Merge-write into ``tenant.config.brand`` — only the subset this
    schema whitelists can be set. Other ``config`` keys (default_currency
    overrides, enabled providers, …) are preserved verbatim."""
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found.")
    config = dict(tenant.config or {})
    existing = dict(config.get("brand") or {})
    patch = data.model_dump(exclude_none=False, by_alias=True)
    for key, value in patch.items():
        if value is None:
            existing.pop(key, None)
        else:
            existing[key] = value
    config["brand"] = existing
    tenant.config = config
    # SQLAlchemy doesn't detect mutations inside JSONB by default; force it.
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(tenant, "config")
    await db.flush()
    return _brand_from_config(config)
