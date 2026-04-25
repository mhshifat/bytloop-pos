from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.modules.shifts.entity import ShiftStatus


class OpenShiftRequest(CamelModel):
    opening_float_cents: int = Field(ge=0)


class CloseShiftRequest(CamelModel):
    closing_counted_cents: int = Field(ge=0)


class ShiftRead(CamelModel):
    id: UUID
    status: ShiftStatus
    opening_float_cents: int
    closing_counted_cents: int | None
    expected_cash_cents: int | None
    variance_cents: int | None
    opened_at: datetime
    closed_at: datetime | None
