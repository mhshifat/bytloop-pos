from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.verticals.retail.pet_store.entity import PetProductMetadata


class PetStoreService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_metadata(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        target_species: str | None = None,
        target_breed: str | None = None,
        life_stage: str | None = None,
        weight_range_lbs: str | None = None,
        is_prescription_food: bool = False,
    ) -> PetProductMetadata:
        """Create or update the pet metadata row for a product.

        We do a SELECT-then-INSERT/UPDATE rather than ``INSERT ... ON CONFLICT``
        because the table is tiny (one row per pet SKU) and the explicit path
        plays nicely with the tenant check — we never want to update a row
        whose ``tenant_id`` doesn't match the caller.
        """
        row = await self._session.get(PetProductMetadata, product_id)
        if row is None:
            row = PetProductMetadata(
                product_id=product_id,
                tenant_id=tenant_id,
                target_species=target_species,
                target_breed=target_breed,
                life_stage=life_stage,
                weight_range_lbs=weight_range_lbs,
                is_prescription_food=is_prescription_food,
            )
            self._session.add(row)
        else:
            if row.tenant_id != tenant_id:
                # Treat cross-tenant lookups as "doesn't exist for you" — we
                # don't leak the fact that another tenant has metadata here.
                raise NotFoundError("Pet product metadata not found.")
            row.target_species = target_species
            row.target_breed = target_breed
            row.life_stage = life_stage
            row.weight_range_lbs = weight_range_lbs
            row.is_prescription_food = is_prescription_food
        await self._session.flush()
        return row

    async def get_for_product(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> PetProductMetadata:
        row = await self._session.get(PetProductMetadata, product_id)
        if row is None or row.tenant_id != tenant_id:
            raise NotFoundError("Pet product metadata not found.")
        return row

    async def list_by_species(
        self, *, tenant_id: UUID, species: str
    ) -> list[PetProductMetadata]:
        stmt = (
            select(PetProductMetadata)
            .where(
                PetProductMetadata.tenant_id == tenant_id,
                PetProductMetadata.target_species == species,
            )
            .order_by(PetProductMetadata.product_id)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_prescription_foods(
        self, *, tenant_id: UUID
    ) -> list[PetProductMetadata]:
        stmt = (
            select(PetProductMetadata)
            .where(
                PetProductMetadata.tenant_id == tenant_id,
                PetProductMetadata.is_prescription_food.is_(True),
            )
            .order_by(PetProductMetadata.product_id)
        )
        return list((await self._session.execute(stmt)).scalars().all())
