from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.retail.grocery.entity import GrocerySku, PluCode, SellUnit


@dataclass(frozen=True, slots=True)
class ScaleLabel:
    """Decoded price-embedded EAN-13 from a deli/produce scale.

    Format: leading digit 2, then 5-digit PLU/item code, then 5-digit
    encoded value (either grams or cents depending on the scale setup),
    then check digit. We store both interpretations and let the service
    decide which to use based on the product's SellUnit.
    """

    plu_or_item: str
    encoded_value: int  # grams or cents
    raw: str


class GroceryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lookup_by_plu(self, *, tenant_id: UUID, code: str) -> UUID:
        stmt = select(PluCode).where(
            PluCode.tenant_id == tenant_id, PluCode.code == code
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Unknown PLU code.")
        return row.product_id

    async def register_plu(
        self, *, tenant_id: UUID, code: str, product_id: UUID
    ) -> PluCode:
        existing = await self._session.execute(
            select(PluCode).where(
                PluCode.tenant_id == tenant_id, PluCode.code == code
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("That PLU code is already in use.")
        plu = PluCode(tenant_id=tenant_id, code=code, product_id=product_id)
        self._session.add(plu)
        await self._session.flush()
        return plu

    async def upsert_weighable(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        sell_unit: SellUnit,
        price_per_unit_cents: int,
        tare_grams: int,
    ) -> GrocerySku:
        stmt = select(GrocerySku).where(
            GrocerySku.tenant_id == tenant_id, GrocerySku.product_id == product_id
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.sell_unit = sell_unit
            existing.price_per_unit_cents = price_per_unit_cents
            existing.tare_grams = tare_grams
            await self._session.flush()
            return existing
        sku = GrocerySku(
            product_id=product_id,
            tenant_id=tenant_id,
            sell_unit=sell_unit,
            price_per_unit_cents=price_per_unit_cents,
            tare_grams=tare_grams,
        )
        self._session.add(sku)
        await self._session.flush()
        return sku

    async def price_by_weight(
        self, *, tenant_id: UUID, product_id: UUID, grams: int
    ) -> int:
        stmt = select(GrocerySku).where(
            GrocerySku.tenant_id == tenant_id, GrocerySku.product_id == product_id
        )
        sku = (await self._session.execute(stmt)).scalar_one_or_none()
        if sku is None:
            raise NotFoundError("Product isn't configured as weighable.")
        net = max(0, grams - sku.tare_grams)
        if sku.sell_unit == SellUnit.KG:
            return int(round(sku.price_per_unit_cents * (net / 1000.0)))
        if sku.sell_unit == SellUnit.G:
            return int(round(sku.price_per_unit_cents * net))
        if sku.sell_unit == SellUnit.LB:
            return int(round(sku.price_per_unit_cents * (net / 453.592)))
        return sku.price_per_unit_cents

    @staticmethod
    def decode_scale_label(barcode: str) -> ScaleLabel | None:
        """Decode a price-embedded EAN-13 from a weighing scale.

        Only returns when the barcode starts with ``2`` and is 13 digits —
        otherwise the caller should treat this as a regular barcode.
        """
        if len(barcode) != 13 or not barcode.isdigit() or barcode[0] != "2":
            return None
        plu = barcode[1:6]
        encoded = int(barcode[6:11])
        return ScaleLabel(plu_or_item=plu, encoded_value=encoded, raw=barcode)

    async def resolve_scan(
        self, *, tenant_id: UUID, input_code: str
    ) -> tuple[UUID, int | None]:
        """Turn a cashier input into (product_id, line_total_cents?).

        Tries: price-embedded scale label → PLU lookup → raises NotFound.
        Returns a line_total when the scale label already encodes one.
        """
        label = self.decode_scale_label(input_code)
        if label is not None:
            # Look up the PLU (5-digit form, trim leading zeros to the 4-digit
            # one we actually store).
            plu_str = label.plu_or_item.lstrip("0") or "0"
            product_id = await self.lookup_by_plu(tenant_id=tenant_id, code=plu_str)
            stmt = select(GrocerySku).where(
                GrocerySku.tenant_id == tenant_id, GrocerySku.product_id == product_id
            )
            sku = (await self._session.execute(stmt)).scalar_one_or_none()
            if sku is None:
                return product_id, None
            # Scales in many BD/EU regions encode price in the last 5 digits
            # for each-priced items, and grams for weighable ones. If the
            # product sells by weight, treat the encoded value as grams.
            if sku.sell_unit in (SellUnit.KG, SellUnit.G, SellUnit.LB):
                line_total = await self.price_by_weight(
                    tenant_id=tenant_id,
                    product_id=product_id,
                    grams=label.encoded_value,
                )
                return product_id, line_total
            return product_id, label.encoded_value

        # Plain PLU (4-digit produce code)
        if input_code.isdigit() and 3 <= len(input_code) <= 5:
            product_id = await self.lookup_by_plu(
                tenant_id=tenant_id, code=input_code
            )
            return product_id, None

        raise NotFoundError("Unrecognised scan input.")
