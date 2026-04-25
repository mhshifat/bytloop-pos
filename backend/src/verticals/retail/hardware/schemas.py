from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class QuantityBreakRead(CamelModel):
    id: UUID
    product_id: UUID
    min_quantity: int
    unit_price_cents: int


class QuantityBreakTier(CamelModel):
    """A single rung submitted when replacing the ladder."""

    min_quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)


class SetBreaksRequest(CamelModel):
    product_id: UUID
    tiers: list[QuantityBreakTier] = Field(default_factory=list)


class ResolvePriceRequest(CamelModel):
    product_id: UUID
    quantity: int = Field(ge=1)


class ResolvedPrice(CamelModel):
    product_id: UUID
    quantity: int
    unit_price_cents: int
    # ``None`` when we fell back to Product.price_cents (no matching tier).
    matched_min_quantity: int | None = None
