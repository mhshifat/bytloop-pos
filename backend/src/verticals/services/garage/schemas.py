from __future__ import annotations

from uuid import UUID

from pydantic import Field

from datetime import datetime

from src.core.schemas import CamelModel
from src.verticals.services.garage.entity import JobCardStatus, JobLineKind


class VehicleRead(CamelModel):
    id: UUID
    plate: str
    make: str
    model: str
    year: int | None
    vin: str | None
    customer_id: UUID | None


class VehicleCreate(CamelModel):
    plate: str = Field(min_length=1, max_length=16)
    make: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=64)
    year: int | None = None
    vin: str | None = None
    customer_id: UUID | None = None


class JobCardRead(CamelModel):
    id: UUID
    vehicle_id: UUID
    technician_id: UUID | None
    status: JobCardStatus
    description: str
    order_id: UUID | None


class JobCardCreate(CamelModel):
    vehicle_id: UUID
    description: str = ""
    technician_id: UUID | None = None


class UpdateJobStatusRequest(CamelModel):
    status: JobCardStatus


class JobLineRead(CamelModel):
    id: UUID
    job_card_id: UUID
    kind: JobLineKind
    product_id: UUID | None
    description: str
    quantity: int
    unit_cost_cents: int
    line_total_cents: int
    created_at: datetime


class JobLineCreate(CamelModel):
    kind: JobLineKind
    description: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, default=1)
    unit_cost_cents: int = Field(ge=0)
    product_id: UUID | None = None


class JobTotalsRead(CamelModel):
    parts_cents: int
    labor_cents: int
    total_cents: int


class VehicleHistoryItem(CamelModel):
    id: UUID
    status: JobCardStatus
    description: str
    opened_at: datetime
    closed_at: datetime | None
