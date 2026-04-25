from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.services.salon.entity import AppointmentStatus


class AppointmentRead(CamelModel):
    id: UUID
    customer_id: UUID
    staff_id: UUID | None
    service_id: UUID | None = None
    service_name: str
    status: AppointmentStatus
    starts_at: datetime
    ends_at: datetime
    order_id: UUID | None = None


class AppointmentCreate(CamelModel):
    customer_id: UUID
    staff_id: UUID | None = None
    service_id: UUID | None = None
    service_name: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime


class UpdateAppointmentStatusRequest(CamelModel):
    status: AppointmentStatus


class SalonServiceRead(CamelModel):
    id: UUID
    code: str
    name: str
    duration_minutes: int
    price_cents: int
    is_active: bool
    product_id: UUID | None


class SalonServiceUpsert(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    duration_minutes: int = Field(ge=5, le=600)
    price_cents: int = Field(ge=0)
    product_id: UUID | None = None
    is_active: bool = True


class AvailabilityWindow(CamelModel):
    starts_at: datetime
    ends_at: datetime


class CheckInResponse(CamelModel):
    appointment: AppointmentRead
    product_id: UUID | None = None
