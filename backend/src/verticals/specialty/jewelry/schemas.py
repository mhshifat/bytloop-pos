from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class JewelryAttributeRead(CamelModel):
    product_id: UUID
    metal: str
    karat: int
    gross_grams: Decimal
    net_grams: Decimal
    making_charge_pct: Decimal
    making_charge_per_gram_cents: int
    wastage_pct: Decimal
    stone_value_cents: int
    certificate_no: str | None


class JewelryAttributeUpsert(CamelModel):
    product_id: UUID
    metal: str = Field(default="gold", max_length=16)
    karat: int = Field(ge=1, le=24)
    gross_grams: Decimal = Field(ge=Decimal("0"))
    net_grams: Decimal = Field(ge=Decimal("0"))
    making_charge_pct: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("100"))
    making_charge_per_gram_cents: int = Field(default=0, ge=0)
    wastage_pct: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))
    stone_value_cents: int = Field(default=0, ge=0)
    certificate_no: str | None = None


class MetalRateUpsert(CamelModel):
    metal: str = Field(default="gold", max_length=16)
    karat: int = Field(ge=1, le=24)
    rate_per_gram_cents: int = Field(ge=0)
    effective_on: date


class MetalRateRead(CamelModel):
    id: UUID
    metal: str
    karat: int
    rate_per_gram_cents: int
    effective_on: date


class JewelryQuoteRead(CamelModel):
    product_id: UUID
    metal_value_cents: int
    wastage_cents: int
    making_charge_cents: int
    stone_value_cents: int
    total_cents: int
