from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.services.rfid_memberships.entity import PassStatus


class RfidPassRead(CamelModel):
    id: UUID
    rfid_tag: str
    customer_id: UUID | None = None
    plan_code: str
    balance_uses: int | None = None
    expires_on: date | None = None
    status: PassStatus
    created_at: datetime


class IssuePassRequest(CamelModel):
    rfid_tag: str = Field(min_length=1, max_length=64)
    customer_id: UUID | None = None
    plan_code: str = Field(min_length=1, max_length=64)
    balance_uses: int | None = Field(default=None, ge=0)
    expires_on: date | None = None


class UpdatePassStatusRequest(CamelModel):
    status: PassStatus


class RedeemRequest(CamelModel):
    rfid_tag: str = Field(min_length=1, max_length=64)
    location: str = Field(default="", max_length=64)


class RedeemResult(CamelModel):
    success: bool
    reason: str | None = None
    pass_id: UUID | None = None
    balance_uses_remaining: int | None = None


class PassUseRead(CamelModel):
    id: UUID
    pass_id: UUID
    location: str
    used_at: datetime
