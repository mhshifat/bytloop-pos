from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class ResortPackageRead(CamelModel):
    id: UUID
    code: str
    name: str
    per_night_price_cents: int
    includes_meals: bool
    includes_drinks: bool
    includes_spa: bool
    includes_activities: bool


class ResortPackageCreate(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    per_night_price_cents: int = Field(ge=0)
    includes_meals: bool = True
    includes_drinks: bool = False
    includes_spa: bool = False
    includes_activities: bool = False


class ResortPackageBookingRead(CamelModel):
    id: UUID
    reservation_id: UUID
    package_code: str
    nights: int
    total_package_cents: int
    attached_at: datetime


class AttachPackageRequest(CamelModel):
    package_code: str = Field(min_length=1, max_length=64)
    nights: int = Field(ge=1)


class AmenitiesRead(CamelModel):
    reservation_id: UUID
    package_code: str
    includes_meals: bool
    includes_drinks: bool
    includes_spa: bool
    includes_activities: bool
