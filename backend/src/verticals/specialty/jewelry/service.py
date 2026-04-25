from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.verticals.specialty.jewelry.entity import (
    DailyMetalRate,
    JewelryAttribute,
)


@dataclass(frozen=True, slots=True)
class JewelryQuote:
    metal_value_cents: int
    wastage_cents: int
    making_charge_cents: int
    stone_value_cents: int
    total_cents: int


class JewelryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Attribute CRUD
    # ──────────────────────────────────────────────

    async def upsert_attribute(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        metal: str,
        karat: int,
        gross_grams: Decimal,
        net_grams: Decimal,
        making_charge_pct: Decimal,
        making_charge_per_gram_cents: int,
        wastage_pct: Decimal,
        stone_value_cents: int,
        certificate_no: str | None,
    ) -> JewelryAttribute:
        stmt = select(JewelryAttribute).where(
            JewelryAttribute.tenant_id == tenant_id,
            JewelryAttribute.product_id == product_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.metal = metal
            existing.karat = karat
            existing.gross_grams = gross_grams
            existing.net_grams = net_grams
            existing.making_charge_pct = making_charge_pct
            existing.making_charge_per_gram_cents = making_charge_per_gram_cents
            existing.wastage_pct = wastage_pct
            existing.stone_value_cents = stone_value_cents
            existing.certificate_no = certificate_no
            await self._session.flush()
            return existing

        attribute = JewelryAttribute(
            product_id=product_id,
            tenant_id=tenant_id,
            metal=metal,
            karat=karat,
            gross_grams=gross_grams,
            net_grams=net_grams,
            making_charge_pct=making_charge_pct,
            making_charge_per_gram_cents=making_charge_per_gram_cents,
            wastage_pct=wastage_pct,
            stone_value_cents=stone_value_cents,
            certificate_no=certificate_no,
        )
        self._session.add(attribute)
        await self._session.flush()
        return attribute

    async def get(self, *, tenant_id: UUID, product_id: UUID) -> JewelryAttribute:
        stmt = select(JewelryAttribute).where(
            JewelryAttribute.tenant_id == tenant_id,
            JewelryAttribute.product_id == product_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Jewelry attributes not set for that product.")
        return row

    # ──────────────────────────────────────────────
    # Daily rates
    # ──────────────────────────────────────────────

    async def set_rate(
        self,
        *,
        tenant_id: UUID,
        metal: str,
        karat: int,
        rate_per_gram_cents: int,
        effective_on: date,
    ) -> DailyMetalRate:
        stmt = select(DailyMetalRate).where(
            DailyMetalRate.tenant_id == tenant_id,
            DailyMetalRate.metal == metal,
            DailyMetalRate.karat == karat,
            DailyMetalRate.effective_on == effective_on,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.rate_per_gram_cents = rate_per_gram_cents
            await self._session.flush()
            return existing
        rate = DailyMetalRate(
            tenant_id=tenant_id,
            metal=metal,
            karat=karat,
            rate_per_gram_cents=rate_per_gram_cents,
            effective_on=effective_on,
        )
        self._session.add(rate)
        await self._session.flush()
        return rate

    async def current_rate(
        self, *, tenant_id: UUID, metal: str, karat: int, on_date: date | None = None
    ) -> DailyMetalRate:
        target = on_date or date.today()
        stmt = (
            select(DailyMetalRate)
            .where(
                DailyMetalRate.tenant_id == tenant_id,
                DailyMetalRate.metal == metal,
                DailyMetalRate.karat == karat,
                DailyMetalRate.effective_on <= target,
            )
            .order_by(DailyMetalRate.effective_on.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError(
                f"No metal rate set for {metal} {karat}k. Set today's rate first."
            )
        return row

    async def list_rates(
        self, *, tenant_id: UUID, on_date: date | None = None
    ) -> list[DailyMetalRate]:
        """Most recent rate per (metal, karat) up to the given date."""
        target = on_date or date.today()
        stmt = (
            select(DailyMetalRate)
            .where(
                DailyMetalRate.tenant_id == tenant_id,
                DailyMetalRate.effective_on <= target,
            )
            .order_by(
                DailyMetalRate.metal,
                DailyMetalRate.karat,
                DailyMetalRate.effective_on.desc(),
            )
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        # Deduplicate to keep only the most recent rate per (metal, karat).
        seen: dict[tuple[str, int], DailyMetalRate] = {}
        for r in rows:
            key = (r.metal, r.karat)
            if key not in seen:
                seen[key] = r
        return list(seen.values())

    # ──────────────────────────────────────────────
    # Price calculation
    # ──────────────────────────────────────────────

    async def quote(
        self, *, tenant_id: UUID, product_id: UUID, on_date: date | None = None
    ) -> JewelryQuote:
        """Combine today's metal rate + attribute to produce a sellable price.

        formula:
            metal_value   = net_grams * rate_per_gram
            wastage       = metal_value * wastage_pct
            making        = metal_value * making_pct  (or grams * per_gram if pct=0)
            total         = metal + wastage + making + stone_value
        """
        attr = await self.get(tenant_id=tenant_id, product_id=product_id)
        rate = await self.current_rate(
            tenant_id=tenant_id, metal=attr.metal, karat=attr.karat, on_date=on_date
        )

        metal_value_cents = int(
            round(float(attr.net_grams) * rate.rate_per_gram_cents)
        )
        wastage_cents = int(
            round(metal_value_cents * float(attr.wastage_pct) / 100)
        )
        if attr.making_charge_pct > 0:
            making_cents = int(
                round(metal_value_cents * float(attr.making_charge_pct) / 100)
            )
        else:
            making_cents = int(
                round(float(attr.gross_grams) * attr.making_charge_per_gram_cents)
            )
        total = (
            metal_value_cents + wastage_cents + making_cents + attr.stone_value_cents
        )
        return JewelryQuote(
            metal_value_cents=metal_value_cents,
            wastage_cents=wastage_cents,
            making_charge_cents=making_cents,
            stone_value_cents=attr.stone_value_cents,
            total_cents=total,
        )
