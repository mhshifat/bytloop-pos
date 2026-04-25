from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class TaxRuleRead(CamelModel):
    id: UUID
    code: str
    name: str
    rate: Decimal
    is_inclusive: bool
    is_active: bool


class TaxRuleCreate(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    is_inclusive: bool = False
