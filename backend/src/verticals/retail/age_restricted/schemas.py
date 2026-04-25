from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class AgeRestrictedProductRead(CamelModel):
    product_id: UUID
    min_age_years: int


class SetMinAgeRequest(CamelModel):
    product_id: UUID
    min_age_years: int = Field(ge=0, le=120)


class RequiresVerificationRequest(CamelModel):
    product_ids: list[UUID] = Field(default_factory=list)


class RequiresVerificationItem(CamelModel):
    product_id: UUID
    min_age_years: int


class VerifyRequest(CamelModel):
    order_id: UUID
    # ISO string (YYYY-MM-DD). Pydantic coerces to ``date``.
    customer_dob: date
    verified_by_user_id: UUID


class AgeVerificationLogRead(CamelModel):
    id: UUID
    order_id: UUID | None
    verified_by_user_id: UUID | None
    customer_dob: date
    min_age_required: int
    verified_age_years: int
    created_at: datetime
