from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.retail.florist.entity import (
    BouquetComponent,
    BouquetInstance,
    BouquetInstanceItem,
    BouquetTemplate,
)


class ComposeItem:
    """Internal mirror of the compose request item — kept here so the service
    stays independent of the router's Pydantic types."""

    __slots__ = ("component_name", "quantity", "unit_price_cents")

    def __init__(self, *, component_name: str, quantity: int, unit_price_cents: int) -> None:
        self.component_name = component_name
        self.quantity = quantity
        self.unit_price_cents = unit_price_cents


class FloristService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── templates ────────────────────────────────────────────────────

    async def create_template(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        base_price_cents: int,
    ) -> BouquetTemplate:
        # Pre-check the unique constraint so we surface a clean ConflictError
        # instead of letting an IntegrityError bubble up at flush.
        existing = (
            await self._session.execute(
                select(BouquetTemplate).where(
                    BouquetTemplate.tenant_id == tenant_id,
                    BouquetTemplate.code == code,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("A template with that code already exists.")
        template = BouquetTemplate(
            tenant_id=tenant_id,
            code=code,
            name=name,
            base_price_cents=base_price_cents,
        )
        self._session.add(template)
        await self._session.flush()
        return template

    async def list_templates(self, *, tenant_id: UUID) -> list[BouquetTemplate]:
        stmt = (
            select(BouquetTemplate)
            .where(BouquetTemplate.tenant_id == tenant_id)
            .order_by(BouquetTemplate.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_template(
        self, *, tenant_id: UUID, template_id: UUID
    ) -> BouquetTemplate:
        template = await self._session.get(BouquetTemplate, template_id)
        if template is None or template.tenant_id != tenant_id:
            raise NotFoundError("Bouquet template not found.")
        return template

    # ── components ───────────────────────────────────────────────────

    async def add_component(
        self,
        *,
        tenant_id: UUID,
        template_id: UUID,
        component_name: str,
        default_quantity: int,
        unit_price_cents: int,
    ) -> BouquetComponent:
        # Verify the template belongs to this tenant before attaching.
        await self._get_template(tenant_id=tenant_id, template_id=template_id)
        component = BouquetComponent(
            tenant_id=tenant_id,
            template_id=template_id,
            component_name=component_name,
            default_quantity=default_quantity,
            unit_price_cents=unit_price_cents,
        )
        self._session.add(component)
        await self._session.flush()
        return component

    async def list_components(
        self, *, tenant_id: UUID, template_id: UUID
    ) -> list[BouquetComponent]:
        await self._get_template(tenant_id=tenant_id, template_id=template_id)
        stmt = (
            select(BouquetComponent)
            .where(
                BouquetComponent.tenant_id == tenant_id,
                BouquetComponent.template_id == template_id,
            )
            .order_by(BouquetComponent.component_name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ── instances ────────────────────────────────────────────────────

    async def compose(
        self,
        *,
        tenant_id: UUID,
        template_id: UUID | None = None,
        items: list[ComposeItem] | None = None,
        wrap_style: str | None = None,
        card_message: str | None = None,
        delivery_schedule_id: UUID | None = None,
    ) -> tuple[BouquetInstance, list[BouquetInstanceItem]]:
        """Create a bouquet instance.

        Exactly one of ``template_id`` or ``items`` must be supplied. When a
        template is chosen we copy its current components (snapshotting the
        default quantity and unit price) so that later edits to the template
        don't rewrite this instance's sale record. When ``items`` is supplied
        we use them verbatim — the bespoke path.
        """
        if (template_id is None) == (items is None):
            raise ValidationError(
                "Provide either a template to copy or an explicit item list."
            )

        resolved_items: list[ComposeItem] = []
        base_price_cents = 0

        if template_id is not None:
            template = await self._get_template(
                tenant_id=tenant_id, template_id=template_id
            )
            base_price_cents = template.base_price_cents
            components = await self.list_components(
                tenant_id=tenant_id, template_id=template_id
            )
            resolved_items = [
                ComposeItem(
                    component_name=c.component_name,
                    quantity=c.default_quantity,
                    unit_price_cents=c.unit_price_cents,
                )
                for c in components
            ]
        else:
            assert items is not None  # narrowed by the XOR check above
            if not items:
                raise ValidationError("A bespoke bouquet needs at least one item.")
            resolved_items = list(items)

        # Line total is the base price (if template) plus each component's
        # quantity * unit price. For bespoke bouquets the base is 0.
        line_total = sum(i.quantity * i.unit_price_cents for i in resolved_items)
        total = base_price_cents + line_total

        instance = BouquetInstance(
            tenant_id=tenant_id,
            total_price_cents=total,
            template_id=template_id,
            order_id=None,
            wrap_style=wrap_style,
            card_message=card_message,
            delivery_schedule_id=delivery_schedule_id,
        )
        self._session.add(instance)
        # Flush once so ``instance.id`` is populated for the FK on each item.
        await self._session.flush()

        persisted_items: list[BouquetInstanceItem] = []
        for i in resolved_items:
            item = BouquetInstanceItem(
                tenant_id=tenant_id,
                instance_id=instance.id,
                component_name=i.component_name,
                quantity=i.quantity,
                unit_price_cents=i.unit_price_cents,
            )
            self._session.add(item)
            persisted_items.append(item)
        await self._session.flush()
        return instance, persisted_items

    async def list_instances(self, *, tenant_id: UUID) -> list[BouquetInstance]:
        stmt = (
            select(BouquetInstance)
            .where(BouquetInstance.tenant_id == tenant_id)
            .order_by(BouquetInstance.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_instance(
        self, *, tenant_id: UUID, instance_id: UUID
    ) -> BouquetInstance:
        instance = await self._session.get(BouquetInstance, instance_id)
        if instance is None or instance.tenant_id != tenant_id:
            raise NotFoundError("Bouquet instance not found.")
        return instance

    async def list_instance_items(
        self, *, tenant_id: UUID, instance_id: UUID
    ) -> list[BouquetInstanceItem]:
        await self.get_instance(tenant_id=tenant_id, instance_id=instance_id)
        stmt = (
            select(BouquetInstanceItem)
            .where(
                BouquetInstanceItem.tenant_id == tenant_id,
                BouquetInstanceItem.instance_id == instance_id,
            )
            .order_by(BouquetInstanceItem.component_name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def link_order(
        self, *, tenant_id: UUID, instance_id: UUID, order_id: UUID
    ) -> BouquetInstance:
        instance = await self.get_instance(
            tenant_id=tenant_id, instance_id=instance_id
        )
        if instance.order_id is not None and instance.order_id != order_id:
            raise ConflictError("Bouquet is already linked to a different order.")
        instance.order_id = order_id
        await self._session.flush()
        return instance
