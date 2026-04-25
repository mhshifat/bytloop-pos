"""Campaign touch tracking for multi-touch attribution (feature 8).

Every inbound visit that can be attributed to a marketing channel writes
a row here: the checkout route + signup route capture UTM params from
``middleware.py`` (downstream) and create one touch per session.

Kept in the ``ai`` module rather than a generic ``marketing`` module
because attribution is currently the only consumer. If we grow a full
campaign-management feature, migrate this to ``modules/marketing/``.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class CampaignTouch(Base):
    __tablename__ = "campaign_touches"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # Free-text channel slug — "google-cpc", "instagram-organic", "email-q3-promo".
    # Kept free-text because each tenant names campaigns differently and we
    # don't want to force a taxonomy on them.
    channel: Mapped[str] = mapped_column(String(64), index=True)
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(64), default=None)
    medium: Mapped[str | None] = mapped_column(String(64), default=None)
    campaign: Mapped[str | None] = mapped_column(String(128), default=None)
    landing_page: Mapped[str | None] = mapped_column(String(255), default=None)
    touched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
