"""SoftPOS — NFC tap-to-pay on merchant phones.

``SoftposReader`` registers the phone itself (one row per device — the
``device_fingerprint`` is the hardware id that the acquiring network
wants to see on every transaction). ``SoftposTapEvent`` is the per-tap
audit ledger.

Compliance note: only the first 6 digits of the card number (the BIN)
are ever stored. Never full PAN — it's not needed for reporting and
keeps the surface out of PCI scope.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class TapOutcome(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    ERROR = "error"


class SoftposReader(Base):
    __tablename__ = "softpos_readers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "device_fingerprint",
            name="uq_softpos_readers_tenant_fingerprint",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    device_label: Mapped[str] = mapped_column(String(128))
    device_fingerprint: Mapped[str] = mapped_column(String(128))
    is_certified: Mapped[bool] = mapped_column(Boolean, default=False)
    certified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class SoftposTapEvent(Base):
    __tablename__ = "softpos_tap_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    reader_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("softpos_readers.id", ondelete="CASCADE"),
        index=True,
    )
    # Strictly 6 chars — the issuer BIN. Enforced at the schema layer too.
    card_bin: Mapped[str] = mapped_column(String(6))
    outcome: Mapped[TapOutcome] = mapped_column(String(16))
    amount_cents: Mapped[int] = mapped_column(default=0)
    provider_reference: Mapped[str | None] = mapped_column(String(128), default=None)
    tapped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
