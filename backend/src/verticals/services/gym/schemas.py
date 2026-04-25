from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.services.gym.entity import MembershipStatus


class MembershipRead(CamelModel):
    id: UUID
    customer_id: UUID
    plan_code: str
    status: MembershipStatus
    starts_on: date
    ends_on: date


class MembershipCreate(CamelModel):
    customer_id: UUID
    plan_code: str = Field(min_length=1, max_length=32)
    starts_on: date
    ends_on: date


class MembershipFromPlan(CamelModel):
    customer_id: UUID
    plan_code: str = Field(min_length=1, max_length=32)
    starts_on: date | None = None


class CheckInRequest(CamelModel):
    membership_id: UUID


class CheckInRead(CamelModel):
    id: UUID
    membership_id: UUID


class PlanRead(CamelModel):
    id: UUID
    code: str
    name: str
    duration_days: int
    price_cents: int
    is_active: bool


class PlanUpsert(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    duration_days: int = Field(ge=1, le=3650)
    price_cents: int = Field(ge=0)
    is_active: bool = True


class ClassRead(CamelModel):
    id: UUID
    title: str
    trainer_id: UUID | None
    starts_at: datetime
    ends_at: datetime
    capacity: int


class ClassCreate(CamelModel):
    title: str = Field(min_length=1, max_length=128)
    trainer_id: UUID | None = None
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(ge=1, le=500)


class ClassBookingRequest(CamelModel):
    membership_id: UUID


class ClassBookingRead(CamelModel):
    id: UUID
    class_id: UUID
    membership_id: UUID
