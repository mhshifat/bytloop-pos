"""Age-restricted sales — minimum-age gate + verification audit.

Two tables on purpose: ``age_restricted_products`` holds the *rule* (which
product needs a minimum age) and ``age_verification_logs`` holds the *event*
(who verified what, when). Keeping them separate lets compliance auditors
query "who sold to under-21s last month" without joining through the live
product catalogue, which may have been edited since.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class AgeRestrictedProduct(Base):
    """Rule row — pins a minimum age to a product.

    Primary key is ``product_id`` so upsert is a simple ``session.merge``
    style operation; one rule per product.
    """

    __tablename__ = "age_restricted_products"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    min_age_years: Mapped[int] = mapped_column(default=18)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class AgeVerificationLog(Base):
    """Immutable audit row — one per successful verification."""

    __tablename__ = "age_verification_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_dob: Mapped[date] = mapped_column(Date)
    # SET NULL so audit history survives order purges/refunds.
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    # Snapshot of the highest min-age at the moment of the sale — keeps the
    # audit trail self-contained if the rule is later relaxed.
    min_age_required: Mapped[int] = mapped_column(default=0)
    verified_age_years: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
