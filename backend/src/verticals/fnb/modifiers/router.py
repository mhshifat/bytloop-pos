from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.modifiers.schemas import (
    AttachGroupRequest,
    ModifierGroupCreate,
    ModifierGroupRead,
    ModifierGroupUpdate,
    ModifierOptionCreate,
    ModifierOptionRead,
    ModifierOptionUpdate,
    PriceLineRequest,
    PriceLineResponse,
)
from src.verticals.fnb.modifiers.service import ModifierService

router = APIRouter(prefix="/modifiers", tags=["modifiers"])


# ──────────────────────────────────────────────
# Groups
# ──────────────────────────────────────────────


@router.get(
    "/groups",
    response_model=list[ModifierGroupRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_groups(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ModifierGroupRead]:
    groups = await ModifierService(db).list_groups(tenant_id=user.tenant_id)
    return [ModifierGroupRead.model_validate(g) for g in groups]


@router.post(
    "/groups",
    response_model=ModifierGroupRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_group(
    data: ModifierGroupCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ModifierGroupRead:
    group = await ModifierService(db).create_group(tenant_id=user.tenant_id, data=data)
    return ModifierGroupRead.model_validate(group)


@router.patch(
    "/groups/{group_id}",
    response_model=ModifierGroupRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def update_group(
    group_id: UUID,
    data: ModifierGroupUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ModifierGroupRead:
    group = await ModifierService(db).update_group(
        tenant_id=user.tenant_id, group_id=group_id, data=data
    )
    return ModifierGroupRead.model_validate(group)


@router.delete(
    "/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def delete_group(
    group_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> Response:
    await ModifierService(db).delete_group(tenant_id=user.tenant_id, group_id=group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Options
# ──────────────────────────────────────────────


@router.get(
    "/groups/{group_id}/options",
    response_model=list[ModifierOptionRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_options(
    group_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ModifierOptionRead]:
    options = await ModifierService(db).list_options(
        tenant_id=user.tenant_id, group_id=group_id
    )
    return [ModifierOptionRead.model_validate(o) for o in options]


@router.post(
    "/groups/{group_id}/options",
    response_model=ModifierOptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_option(
    group_id: UUID,
    data: ModifierOptionCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ModifierOptionRead:
    option = await ModifierService(db).create_option(
        tenant_id=user.tenant_id, group_id=group_id, data=data
    )
    return ModifierOptionRead.model_validate(option)


@router.patch(
    "/options/{option_id}",
    response_model=ModifierOptionRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def update_option(
    option_id: UUID,
    data: ModifierOptionUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ModifierOptionRead:
    option = await ModifierService(db).update_option(
        tenant_id=user.tenant_id, option_id=option_id, data=data
    )
    return ModifierOptionRead.model_validate(option)


@router.delete(
    "/options/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def delete_option(
    option_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> Response:
    await ModifierService(db).delete_option(
        tenant_id=user.tenant_id, option_id=option_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Product attachments
# ──────────────────────────────────────────────


@router.get(
    "/products/{product_id}/groups",
    response_model=list[ModifierGroupRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_for_product(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ModifierGroupRead]:
    groups = await ModifierService(db).list_for_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return [ModifierGroupRead.model_validate(g) for g in groups]


@router.post(
    "/products/{product_id}/groups",
    response_model=ModifierGroupRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def attach_to_product(
    product_id: UUID,
    data: AttachGroupRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ModifierGroupRead:
    svc = ModifierService(db)
    await svc.attach_to_product(
        tenant_id=user.tenant_id,
        product_id=product_id,
        group_id=data.modifier_group_id,
    )
    group = await svc.get_group(tenant_id=user.tenant_id, group_id=data.modifier_group_id)
    return ModifierGroupRead.model_validate(group)


@router.delete(
    "/products/{product_id}/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def detach_from_product(
    product_id: UUID,
    group_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> Response:
    await ModifierService(db).detach_from_product(
        tenant_id=user.tenant_id, product_id=product_id, group_id=group_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Pricing
# ──────────────────────────────────────────────


@router.post(
    "/price-line",
    response_model=PriceLineResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def price_line(
    data: PriceLineRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PriceLineResponse:
    base, delta, total = await ModifierService(db).price_line(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        option_ids=data.option_ids,
    )
    return PriceLineResponse(
        product_id=data.product_id,
        base_price_cents=base,
        modifier_delta_cents=delta,
        total_cents=total,
    )
