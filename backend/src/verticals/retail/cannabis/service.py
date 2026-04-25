from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.verticals.retail.cannabis.entity import (
    BatchState,
    CannabisBatch,
    CannabisTransaction,
    MetrcSyncStatus,
    PurchaseLimit,
    TransactionKind,
)

# Fallback when settings.cannabis isn't wired yet. The config module declares
# CannabisConfig but doesn't attach it to Settings — read defensively.
_DEFAULT_DAILY_GRAM_LIMIT = 28


def _daily_gram_limit() -> Decimal:
    cannabis_cfg = getattr(settings, "cannabis", None)
    if cannabis_cfg is None:
        return Decimal(_DEFAULT_DAILY_GRAM_LIMIT)
    return Decimal(getattr(cannabis_cfg, "daily_gram_limit", _DEFAULT_DAILY_GRAM_LIMIT))


class CannabisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Batches
    # ──────────────────────────────────────────────

    async def list_batches(
        self, *, tenant_id: UUID, state: BatchState | None = None
    ) -> list[CannabisBatch]:
        stmt = select(CannabisBatch).where(CannabisBatch.tenant_id == tenant_id)
        if state is not None:
            stmt = stmt.where(CannabisBatch.state == state)
        stmt = stmt.order_by(CannabisBatch.expires_on)
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_batch(self, *, tenant_id: UUID, batch_id: UUID) -> CannabisBatch:
        batch = await self._session.get(CannabisBatch, batch_id)
        if batch is None or batch.tenant_id != tenant_id:
            raise NotFoundError("Cannabis batch not found.")
        return batch

    async def receive_batch(
        self,
        *,
        tenant_id: UUID,
        batch_id: str,
        product_id: UUID,
        strain_name: str,
        thc_pct: Decimal,
        cbd_pct: Decimal,
        harvested_on: date,
        expires_on: date,
        quantity_grams: Decimal,
        recorded_by_user_id: UUID | None,
    ) -> CannabisBatch:
        """Create a batch plus its initial `received` ledger row."""
        if quantity_grams <= 0:
            raise ValidationError("Received quantity must be positive.")
        # Uniqueness of (tenant_id, batch_id) is enforced at DB level, but check
        # first so we surface a clean 409 instead of an IntegrityError.
        stmt = select(CannabisBatch).where(
            CannabisBatch.tenant_id == tenant_id,
            CannabisBatch.batch_id == batch_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            raise ConflictError(
                f"Batch tag '{batch_id}' already exists for this tenant."
            )
        batch = CannabisBatch(
            tenant_id=tenant_id,
            batch_id=batch_id,
            product_id=product_id,
            strain_name=strain_name,
            thc_pct=thc_pct,
            cbd_pct=cbd_pct,
            harvested_on=harvested_on,
            expires_on=expires_on,
            quantity_grams=quantity_grams,
            state=BatchState.ACTIVE,
        )
        self._session.add(batch)
        await self._session.flush()
        self._session.add(
            CannabisTransaction(
                tenant_id=tenant_id,
                batch_id=batch.id,
                kind=TransactionKind.RECEIVED,
                grams_delta=quantity_grams,
                order_id=None,
                customer_id=None,
                reason=None,
                recorded_by_user_id=recorded_by_user_id,
                metrc_sync_status=MetrcSyncStatus.PENDING,
                metrc_sync_error=None,
            )
        )
        await self._session.flush()
        return batch

    # ──────────────────────────────────────────────
    # Sales gate — daily possession limit
    # ──────────────────────────────────────────────

    async def _customer_grams_today(
        self, *, tenant_id: UUID, customer_id: UUID, day: date
    ) -> PurchaseLimit | None:
        stmt = select(PurchaseLimit).where(
            PurchaseLimit.tenant_id == tenant_id,
            PurchaseLimit.customer_id == customer_id,
            PurchaseLimit.day_date == day,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def sell(
        self,
        *,
        tenant_id: UUID,
        batch_id: UUID,
        customer_id: UUID,
        grams: Decimal,
        order_id: UUID | None,
        recorded_by_user_id: UUID | None,
    ) -> CannabisTransaction:
        """Record a sale against a batch. Enforces daily per-customer limit."""
        if grams <= 0:
            raise ValidationError("Sold grams must be positive.")
        batch = await self.get_batch(tenant_id=tenant_id, batch_id=batch_id)
        if batch.state == BatchState.RECALLED:
            raise ForbiddenError(
                "This batch has been recalled and cannot be sold.",
                code="batch_recalled",
            )
        if Decimal(batch.quantity_grams) < grams:
            raise ConflictError(
                f"Not enough stock in batch: have {batch.quantity_grams}g, need {grams}g."
            )

        today = date.today()
        limit = _daily_gram_limit()
        tally = await self._customer_grams_today(
            tenant_id=tenant_id, customer_id=customer_id, day=today
        )
        current = Decimal(tally.grams_purchased) if tally is not None else Decimal(0)
        if current + grams > limit:
            raise ForbiddenError(
                f"Daily purchase limit of {limit}g exceeded "
                f"(already purchased {current}g today).",
                code="daily_limit_exceeded",
                details={"limit_grams": float(limit), "already_purchased": float(current)},
            )

        # Deduct stock; mark sold_out if we hit zero.
        batch.quantity_grams = Decimal(batch.quantity_grams) - grams
        if batch.quantity_grams == 0:
            batch.state = BatchState.SOLD_OUT

        # Upsert the daily tally.
        if tally is None:
            tally = PurchaseLimit(
                tenant_id=tenant_id,
                customer_id=customer_id,
                day_date=today,
                grams_purchased=grams,
            )
            self._session.add(tally)
        else:
            tally.grams_purchased = current + grams

        txn = CannabisTransaction(
            tenant_id=tenant_id,
            batch_id=batch.id,
            kind=TransactionKind.SOLD,
            grams_delta=-grams,
            order_id=order_id,
            customer_id=customer_id,
            reason=None,
            recorded_by_user_id=recorded_by_user_id,
            metrc_sync_status=MetrcSyncStatus.PENDING,
            metrc_sync_error=None,
        )
        self._session.add(txn)
        await self._session.flush()
        return txn

    async def destroy(
        self,
        *,
        tenant_id: UUID,
        batch_id: UUID,
        grams: Decimal,
        reason: str,
        recorded_by_user_id: UUID | None,
    ) -> CannabisTransaction:
        if grams <= 0:
            raise ValidationError("Destroyed grams must be positive.")
        batch = await self.get_batch(tenant_id=tenant_id, batch_id=batch_id)
        if Decimal(batch.quantity_grams) < grams:
            raise ConflictError(
                f"Cannot destroy {grams}g: only {batch.quantity_grams}g on hand."
            )
        batch.quantity_grams = Decimal(batch.quantity_grams) - grams
        if batch.quantity_grams == 0 and batch.state != BatchState.RECALLED:
            batch.state = BatchState.SOLD_OUT
        txn = CannabisTransaction(
            tenant_id=tenant_id,
            batch_id=batch.id,
            kind=TransactionKind.DESTROYED,
            grams_delta=-grams,
            order_id=None,
            customer_id=None,
            reason=reason,
            recorded_by_user_id=recorded_by_user_id,
            metrc_sync_status=MetrcSyncStatus.PENDING,
            metrc_sync_error=None,
        )
        self._session.add(txn)
        await self._session.flush()
        return txn

    async def recall(
        self,
        *,
        tenant_id: UUID,
        batch_id: UUID,
        reason: str,
        recorded_by_user_id: UUID | None,
    ) -> CannabisTransaction:
        batch = await self.get_batch(tenant_id=tenant_id, batch_id=batch_id)
        remaining = Decimal(batch.quantity_grams)
        batch.state = BatchState.RECALLED
        batch.quantity_grams = Decimal(0)
        txn = CannabisTransaction(
            tenant_id=tenant_id,
            batch_id=batch.id,
            kind=TransactionKind.RECALLED,
            grams_delta=-remaining,
            order_id=None,
            customer_id=None,
            reason=reason,
            recorded_by_user_id=recorded_by_user_id,
            metrc_sync_status=MetrcSyncStatus.PENDING,
            metrc_sync_error=None,
        )
        self._session.add(txn)
        await self._session.flush()
        return txn

    # ──────────────────────────────────────────────
    # METRC sync outbox
    # ──────────────────────────────────────────────

    async def unsynced_transactions(
        self, *, tenant_id: UUID
    ) -> list[CannabisTransaction]:
        stmt = (
            select(CannabisTransaction)
            .where(
                CannabisTransaction.tenant_id == tenant_id,
                CannabisTransaction.metrc_sync_status.in_(
                    [MetrcSyncStatus.PENDING, MetrcSyncStatus.FAILED]
                ),
            )
            .order_by(CannabisTransaction.recorded_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def pending_outbound_all_tenants(
        self, *, limit: int
    ) -> list[CannabisTransaction]:
        """Oldest PENDING/FAILED rows across all tenants (compliance outbox)."""
        stmt = (
            select(CannabisTransaction)
            .where(
                CannabisTransaction.metrc_sync_status.in_(
                    [MetrcSyncStatus.PENDING, MetrcSyncStatus.FAILED]
                )
            )
            .order_by(CannabisTransaction.recorded_at)
            .limit(max(1, min(limit, 500)))
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def mark_synced(
        self, *, tenant_id: UUID, transaction_id: UUID
    ) -> CannabisTransaction:
        txn = await self._session.get(CannabisTransaction, transaction_id)
        if txn is None or txn.tenant_id != tenant_id:
            raise NotFoundError("Cannabis transaction not found.")
        txn.metrc_sync_status = MetrcSyncStatus.SYNCED
        txn.metrc_sync_error = None
        await self._session.flush()
        return txn

    async def mark_sync_failed(
        self, *, tenant_id: UUID, transaction_id: UUID, error: str
    ) -> CannabisTransaction:
        txn = await self._session.get(CannabisTransaction, transaction_id)
        if txn is None or txn.tenant_id != tenant_id:
            raise NotFoundError("Cannabis transaction not found.")
        txn.metrc_sync_status = MetrcSyncStatus.FAILED
        txn.metrc_sync_error = error
        await self._session.flush()
        return txn
