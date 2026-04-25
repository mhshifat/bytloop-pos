from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.modules.catalog.api import CatalogService
from src.verticals.fnb.modifiers.entity import (
    ModifierGroup,
    ModifierOption,
    ProductModifierLink,
)
from src.verticals.fnb.modifiers.schemas import (
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierOptionCreate,
    ModifierOptionUpdate,
)


class ModifierService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        catalog: CatalogService | None = None,
    ) -> None:
        self._session = session
        self._catalog = catalog or CatalogService(session)

    # ──────────────────────────────────────────────
    # Groups
    # ──────────────────────────────────────────────

    async def list_groups(self, *, tenant_id: UUID) -> list[ModifierGroup]:
        stmt = (
            select(ModifierGroup)
            .where(ModifierGroup.tenant_id == tenant_id)
            .order_by(ModifierGroup.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_group(self, *, tenant_id: UUID, group_id: UUID) -> ModifierGroup:
        group = await self._session.get(ModifierGroup, group_id)
        if group is None or group.tenant_id != tenant_id:
            raise NotFoundError("Modifier group not found.")
        return group

    async def create_group(
        self, *, tenant_id: UUID, data: ModifierGroupCreate
    ) -> ModifierGroup:
        if data.max_selections < data.min_selections:
            raise ValidationError(
                "maxSelections must be greater than or equal to minSelections."
            )
        stmt = select(ModifierGroup).where(
            ModifierGroup.tenant_id == tenant_id,
            ModifierGroup.code == data.code,
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("A modifier group with that code already exists.")
        group = ModifierGroup(
            tenant_id=tenant_id,
            code=data.code,
            name=data.name,
            min_selections=data.min_selections,
            max_selections=data.max_selections,
            required=data.required,
        )
        self._session.add(group)
        await self._session.flush()
        return group

    async def update_group(
        self, *, tenant_id: UUID, group_id: UUID, data: ModifierGroupUpdate
    ) -> ModifierGroup:
        group = await self.get_group(tenant_id=tenant_id, group_id=group_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(group, field, value)
        if group.max_selections < group.min_selections:
            raise ValidationError(
                "maxSelections must be greater than or equal to minSelections."
            )
        await self._session.flush()
        return group

    async def delete_group(self, *, tenant_id: UUID, group_id: UUID) -> None:
        group = await self.get_group(tenant_id=tenant_id, group_id=group_id)
        await self._session.delete(group)
        await self._session.flush()

    # ──────────────────────────────────────────────
    # Options
    # ──────────────────────────────────────────────

    async def list_options(
        self, *, tenant_id: UUID, group_id: UUID
    ) -> list[ModifierOption]:
        # Guard tenant ownership of the group.
        await self.get_group(tenant_id=tenant_id, group_id=group_id)
        stmt = (
            select(ModifierOption)
            .where(
                ModifierOption.tenant_id == tenant_id,
                ModifierOption.group_id == group_id,
            )
            .order_by(ModifierOption.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_option(
        self, *, tenant_id: UUID, group_id: UUID, data: ModifierOptionCreate
    ) -> ModifierOption:
        await self.get_group(tenant_id=tenant_id, group_id=group_id)
        option = ModifierOption(
            tenant_id=tenant_id,
            group_id=group_id,
            name=data.name,
            price_cents_delta=data.price_cents_delta,
            is_default=data.is_default,
        )
        self._session.add(option)
        await self._session.flush()
        return option

    async def update_option(
        self,
        *,
        tenant_id: UUID,
        option_id: UUID,
        data: ModifierOptionUpdate,
    ) -> ModifierOption:
        option = await self._session.get(ModifierOption, option_id)
        if option is None or option.tenant_id != tenant_id:
            raise NotFoundError("Modifier option not found.")
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(option, field, value)
        await self._session.flush()
        return option

    async def delete_option(self, *, tenant_id: UUID, option_id: UUID) -> None:
        option = await self._session.get(ModifierOption, option_id)
        if option is None or option.tenant_id != tenant_id:
            raise NotFoundError("Modifier option not found.")
        await self._session.delete(option)
        await self._session.flush()

    # ──────────────────────────────────────────────
    # Product attachment
    # ──────────────────────────────────────────────

    async def list_for_product(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> list[ModifierGroup]:
        # Validate tenant ownership of the product.
        await self._catalog.get_product(tenant_id=tenant_id, product_id=product_id)
        stmt = (
            select(ModifierGroup)
            .join(
                ProductModifierLink,
                ProductModifierLink.modifier_group_id == ModifierGroup.id,
            )
            .where(
                ModifierGroup.tenant_id == tenant_id,
                ProductModifierLink.product_id == product_id,
                ProductModifierLink.tenant_id == tenant_id,
            )
            .order_by(ModifierGroup.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def attach_to_product(
        self, *, tenant_id: UUID, product_id: UUID, group_id: UUID
    ) -> ProductModifierLink:
        await self._catalog.get_product(tenant_id=tenant_id, product_id=product_id)
        await self.get_group(tenant_id=tenant_id, group_id=group_id)
        stmt = select(ProductModifierLink).where(
            ProductModifierLink.product_id == product_id,
            ProductModifierLink.modifier_group_id == group_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        link = ProductModifierLink(
            product_id=product_id,
            modifier_group_id=group_id,
            tenant_id=tenant_id,
        )
        self._session.add(link)
        await self._session.flush()
        return link

    async def detach_from_product(
        self, *, tenant_id: UUID, product_id: UUID, group_id: UUID
    ) -> None:
        stmt = select(ProductModifierLink).where(
            ProductModifierLink.tenant_id == tenant_id,
            ProductModifierLink.product_id == product_id,
            ProductModifierLink.modifier_group_id == group_id,
        )
        link = (await self._session.execute(stmt)).scalar_one_or_none()
        if link is None:
            raise NotFoundError("That group is not attached to that product.")
        await self._session.delete(link)
        await self._session.flush()

    # ──────────────────────────────────────────────
    # Pricing
    # ──────────────────────────────────────────────

    async def price_line(
        self, *, tenant_id: UUID, product_id: UUID, option_ids: list[UUID]
    ) -> tuple[int, int, int]:
        """Return ``(base_price_cents, modifier_delta_cents, total_cents)``.

        The modifier delta sums the signed ``price_cents_delta`` of every
        supplied option (options outside the tenant or not attached via any
        group of the product are rejected).
        """
        product = await self._catalog.get_product(
            tenant_id=tenant_id, product_id=product_id
        )
        if not option_ids:
            return product.price_cents, 0, product.price_cents

        # Validate options: must belong to tenant and their group must be
        # linked to the product.
        stmt = (
            select(ModifierOption)
            .join(ProductModifierLink, ProductModifierLink.modifier_group_id == ModifierOption.group_id)
            .where(
                ModifierOption.tenant_id == tenant_id,
                ModifierOption.id.in_(option_ids),
                ProductModifierLink.product_id == product_id,
                ProductModifierLink.tenant_id == tenant_id,
            )
        )
        options = list((await self._session.execute(stmt)).scalars().all())
        if len(options) != len(set(option_ids)):
            raise ValidationError(
                "One or more modifier options don't belong to that product."
            )
        delta = sum(o.price_cents_delta for o in options)
        total = product.price_cents + delta
        return product.price_cents, delta, total
