from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.florist.schemas import (
    AddComponentRequest,
    BouquetComponentRead,
    BouquetInstanceItemRead,
    BouquetInstanceRead,
    BouquetTemplateRead,
    ComposeRequest,
    CreateTemplateRequest,
    LinkOrderRequest,
)
from src.verticals.retail.florist.service import ComposeItem, FloristService

router = APIRouter(prefix="/florist", tags=["florist"])


# ── templates ─────────────────────────────────────────────────────────


@router.get(
    "/templates",
    response_model=list[BouquetTemplateRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_templates(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BouquetTemplateRead]:
    rows = await FloristService(db).list_templates(tenant_id=user.tenant_id)
    return [BouquetTemplateRead.model_validate(r) for r in rows]


@router.post(
    "/templates",
    response_model=BouquetTemplateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_template(
    req: CreateTemplateRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BouquetTemplateRead:
    template = await FloristService(db).create_template(
        tenant_id=user.tenant_id,
        code=req.code,
        name=req.name,
        base_price_cents=req.base_price_cents,
    )
    return BouquetTemplateRead.model_validate(template)


# ── components ────────────────────────────────────────────────────────


@router.get(
    "/templates/{template_id}/components",
    response_model=list[BouquetComponentRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_components(
    template_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BouquetComponentRead]:
    rows = await FloristService(db).list_components(
        tenant_id=user.tenant_id, template_id=template_id
    )
    return [BouquetComponentRead.model_validate(r) for r in rows]


@router.post(
    "/components",
    response_model=BouquetComponentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def add_component(
    req: AddComponentRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BouquetComponentRead:
    component = await FloristService(db).add_component(
        tenant_id=user.tenant_id,
        template_id=req.template_id,
        component_name=req.component_name,
        default_quantity=req.default_quantity,
        unit_price_cents=req.unit_price_cents,
    )
    return BouquetComponentRead.model_validate(component)


# ── instances ─────────────────────────────────────────────────────────


@router.get(
    "/instances",
    response_model=list[BouquetInstanceRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_instances(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BouquetInstanceRead]:
    rows = await FloristService(db).list_instances(tenant_id=user.tenant_id)
    return [BouquetInstanceRead.model_validate(r) for r in rows]


@router.post(
    "/instances",
    response_model=BouquetInstanceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def compose_instance(
    req: ComposeRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BouquetInstanceRead:
    items = (
        [
            ComposeItem(
                component_name=i.component_name,
                quantity=i.quantity,
                unit_price_cents=i.unit_price_cents,
            )
            for i in req.items
        ]
        if req.items is not None
        else None
    )
    instance, _ = await FloristService(db).compose(
        tenant_id=user.tenant_id,
        template_id=req.template_id,
        items=items,
        wrap_style=req.wrap_style,
        card_message=req.card_message,
        delivery_schedule_id=req.delivery_schedule_id,
    )
    return BouquetInstanceRead.model_validate(instance)


@router.get(
    "/instances/{instance_id}",
    response_model=BouquetInstanceRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_instance(
    instance_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BouquetInstanceRead:
    instance = await FloristService(db).get_instance(
        tenant_id=user.tenant_id, instance_id=instance_id
    )
    return BouquetInstanceRead.model_validate(instance)


@router.get(
    "/instances/{instance_id}/items",
    response_model=list[BouquetInstanceItemRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_instance_items(
    instance_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[BouquetInstanceItemRead]:
    rows = await FloristService(db).list_instance_items(
        tenant_id=user.tenant_id, instance_id=instance_id
    )
    return [BouquetInstanceItemRead.model_validate(r) for r in rows]


@router.post(
    "/instances/{instance_id}/link-order",
    response_model=BouquetInstanceRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def link_order(
    instance_id: UUID,
    req: LinkOrderRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BouquetInstanceRead:
    instance = await FloristService(db).link_order(
        tenant_id=user.tenant_id, instance_id=instance_id, order_id=req.order_id
    )
    return BouquetInstanceRead.model_validate(instance)
