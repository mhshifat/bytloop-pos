from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.services.gas_station.entity import DispenserStatus, FuelType


class FuelDispenserRead(CamelModel):
    id: UUID
    label: str
    fuel_type: FuelType
    price_per_liter_cents: int
    product_id: UUID | None = None
    status: DispenserStatus


class FuelDispenserCreate(CamelModel):
    label: str = Field(min_length=1, max_length=32)
    fuel_type: FuelType
    price_per_liter_cents: int = Field(ge=0)
    product_id: UUID | None = None


class DispenserReadingCreate(CamelModel):
    dispenser_id: UUID
    totalizer_reading: float = Field(ge=0)


class DispenserReadingRead(CamelModel):
    id: UUID
    dispenser_id: UUID
    totalizer_reading: float
    liters_dispensed: float
    order_id: UUID | None = None
    taken_at: datetime
