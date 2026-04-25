from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, ForbiddenError, NotFoundError
from src.modules.catalog.api import CatalogService
from src.modules.sales.api import OrderType, PaymentMethod, SalesService
from src.modules.sales.schemas import CartItemInput
from src.verticals.deployment.self_checkout.entity import (
    SelfCheckoutScan,
    SelfCheckoutSession,
    SelfCheckoutStatus,
)
from src.verticals.retail.age_restricted.api import AgeRestrictedService

# Any scan whose unit price exceeds this threshold gets flagged for a
# staff override. 100k cents ≈ big-ticket item.
HIGH_VALUE_FLAG_THRESHOLD_CENTS = 100_000


class SelfCheckoutService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Sessions
    # ──────────────────────────────────────────────

    async def start_session(
        self,
        *,
        tenant_id: UUID,
        station_label: str,
        customer_identifier: str | None = None,
    ) -> SelfCheckoutSession:
        sess = SelfCheckoutSession(
            tenant_id=tenant_id,
            station_label=station_label,
            customer_identifier=customer_identifier,
            status=SelfCheckoutStatus.SCANNING,
            completed_at=None,
            order_id=None,
        )
        self._session.add(sess)
        await self._session.flush()
        return sess

    async def _get_session(
        self, *, tenant_id: UUID, session_id: UUID
    ) -> SelfCheckoutSession:
        sess = await self._session.get(SelfCheckoutSession, session_id)
        if sess is None or sess.tenant_id != tenant_id:
            raise NotFoundError("Session not found.")
        return sess

    async def get_session(
        self, *, tenant_id: UUID, session_id: UUID
    ) -> SelfCheckoutSession:
        return await self._get_session(tenant_id=tenant_id, session_id=session_id)

    async def list_scans(
        self, *, tenant_id: UUID, session_id: UUID
    ) -> list[SelfCheckoutScan]:
        stmt = (
            select(SelfCheckoutScan)
            .where(
                SelfCheckoutScan.tenant_id == tenant_id,
                SelfCheckoutScan.session_id == session_id,
            )
            .order_by(SelfCheckoutScan.scanned_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Scanning
    # ──────────────────────────────────────────────

    async def scan(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        barcode: str,
        quantity: int = 1,
    ) -> SelfCheckoutScan:
        sess = await self._get_session(tenant_id=tenant_id, session_id=session_id)
        if sess.status not in (
            SelfCheckoutStatus.SCANNING,
            SelfCheckoutStatus.AWAITING_APPROVAL,
        ):
            raise ConflictError(
                f"Can't scan into a {sess.status.value} session."
            )

        product = await CatalogService(self._session).find_by_barcode(
            tenant_id=tenant_id, barcode=barcode
        )

        flagged = False
        flag_reason: str | None = None
        unit_price = 0
        product_id: UUID | None = None

        if product is None:
            flagged = True
            flag_reason = "unrecognized_barcode"
        else:
            product_id = product.id
            unit_price = product.price_cents

            # Age-restricted check — ask the cross-vertical service whether
            # a rule exists for this product. Absence of rule = no flag.
            rules = await AgeRestrictedService(self._session).requires_verification(
                tenant_id=tenant_id, product_ids=[product.id]
            )
            if rules:
                flagged = True
                flag_reason = "age_check"
            elif unit_price * quantity >= HIGH_VALUE_FLAG_THRESHOLD_CENTS:
                flagged = True
                flag_reason = "high_value"

        scan = SelfCheckoutScan(
            tenant_id=tenant_id,
            session_id=session_id,
            barcode=barcode,
            product_id=product_id,
            quantity=quantity,
            unit_price_cents=unit_price,
            flagged_for_staff=flagged,
            flag_reason=flag_reason,
        )
        self._session.add(scan)

        # Move the session into AWAITING_APPROVAL as soon as anything is
        # flagged so the UI can tint the staff-call light right away.
        if flagged and sess.status == SelfCheckoutStatus.SCANNING:
            sess.status = SelfCheckoutStatus.AWAITING_APPROVAL

        await self._session.flush()
        return scan

    # ──────────────────────────────────────────────
    # Completion / abandonment
    # ──────────────────────────────────────────────

    async def complete_session(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        staff_user_id: UUID | None = None,
    ) -> SelfCheckoutSession:
        sess = await self._get_session(tenant_id=tenant_id, session_id=session_id)
        if sess.status == SelfCheckoutStatus.COMPLETED:
            raise ConflictError("Session is already completed.")
        if sess.status == SelfCheckoutStatus.ABANDONED:
            raise ConflictError("Session was abandoned and cannot be completed.")

        scans = await self.list_scans(tenant_id=tenant_id, session_id=session_id)
        if not scans:
            raise ConflictError("Cannot complete an empty session.")

        # Drop unrecognized-barcode lines from the cart — they can't be
        # turned into order items. A staff override lets the rest through.
        recognized = [s for s in scans if s.product_id is not None]
        if not recognized:
            raise ConflictError("No recognized items to check out.")

        has_flag = any(s.flagged_for_staff for s in scans)
        if has_flag and staff_user_id is None:
            raise ForbiddenError(
                "Staff approval required for flagged items."
            )

        # Staff member drives the sale when overriding; otherwise the
        # session's own order is recorded against the staff id if given,
        # falling back to a sentinel tenant-admin id is out of scope here
        # so we require staff_user_id in the unflagged case as well if we
        # don't have a better cashier identity. Pragma: the cashier_id
        # column is nullable, so we pass None when we have nothing.
        cashier_id = staff_user_id

        items = [
            CartItemInput(product_id=s.product_id, quantity=s.quantity)  # type: ignore[arg-type]
            for s in recognized
        ]

        completed = await SalesService(self._session).checkout(
            tenant_id=tenant_id,
            cashier_id=cashier_id,  # type: ignore[arg-type]
            items=items,
            order_type=OrderType.RETAIL,
            payment_method=PaymentMethod.CARD,
            amount_tendered_cents=None,
        )

        sess.order_id = completed.order.id
        sess.status = SelfCheckoutStatus.COMPLETED
        sess.completed_at = datetime.now(tz=UTC)
        await self._session.flush()
        return sess

    async def abandon_session(
        self, *, tenant_id: UUID, session_id: UUID
    ) -> SelfCheckoutSession:
        sess = await self._get_session(tenant_id=tenant_id, session_id=session_id)
        if sess.status == SelfCheckoutStatus.COMPLETED:
            raise ConflictError("Cannot abandon a completed session.")
        sess.status = SelfCheckoutStatus.ABANDONED
        sess.completed_at = datetime.now(tz=UTC)
        await self._session.flush()
        return sess
