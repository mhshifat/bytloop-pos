from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.deployment.self_checkout.entity import SelfCheckoutStatus


class SelfCheckoutSessionRead(CamelModel):
    id: UUID
    station_label: str
    customer_identifier: str | None = None
    status: SelfCheckoutStatus
    started_at: datetime
    completed_at: datetime | None = None
    order_id: UUID | None = None


class SelfCheckoutScanRead(CamelModel):
    id: UUID
    session_id: UUID
    barcode: str
    product_id: UUID | None = None
    quantity: int
    unit_price_cents: int
    scanned_at: datetime
    flagged_for_staff: bool
    flag_reason: str | None = None


class StartSessionRequest(CamelModel):
    station_label: str = Field(min_length=1, max_length=64)
    customer_identifier: str | None = Field(default=None, max_length=128)


class ScanRequest(CamelModel):
    barcode: str = Field(min_length=1, max_length=64)
    quantity: int = Field(default=1, ge=1)


class CompleteSessionRequest(CamelModel):
    # Required when any scan was flagged (age_check / high_value /
    # unrecognized_barcode); otherwise optional.
    staff_user_id: UUID | None = None
