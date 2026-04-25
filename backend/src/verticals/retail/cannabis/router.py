from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.cannabis.entity import BatchState
from src.verticals.retail.cannabis.schemas import (
    BatchCreate,
    BatchRead,
    DestroyRequest,
    MarkSyncFailedRequest,
    RecallRequest,
    SellRequest,
    TransactionRead,
)
from src.verticals.retail.cannabis.service import CannabisService

router = APIRouter(prefix="/cannabis", tags=["cannabis"])


@router.get(
    "/batches",
    response_model=list[BatchRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_batches(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    state: BatchState | None = Query(default=None),
) -> list[BatchRead]:
    rows = await CannabisService(db).list_batches(
        tenant_id=user.tenant_id, state=state
    )
    return [BatchRead.model_validate(r) for r in rows]


@router.get(
    "/batches/{batch_id}",
    response_model=BatchRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_batch(
    batch_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BatchRead:
    batch = await CannabisService(db).get_batch(
        tenant_id=user.tenant_id, batch_id=batch_id
    )
    return BatchRead.model_validate(batch)


@router.post(
    "/batches",
    response_model=BatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def receive_batch(
    data: BatchCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BatchRead:
    batch = await CannabisService(db).receive_batch(
        tenant_id=user.tenant_id,
        batch_id=data.batch_id,
        product_id=data.product_id,
        strain_name=data.strain_name,
        thc_pct=data.thc_pct,
        cbd_pct=data.cbd_pct,
        harvested_on=data.harvested_on,
        expires_on=data.expires_on,
        quantity_grams=data.quantity_grams,
        recorded_by_user_id=user.id,
    )
    return BatchRead.model_validate(batch)


@router.post(
    "/sell",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def sell(
    data: SellRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransactionRead:
    txn = await CannabisService(db).sell(
        tenant_id=user.tenant_id,
        batch_id=data.batch_id,
        customer_id=data.customer_id,
        grams=data.grams,
        order_id=data.order_id,
        recorded_by_user_id=user.id,
    )
    return TransactionRead.model_validate(txn)


@router.post(
    "/destroy",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def destroy(
    data: DestroyRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransactionRead:
    txn = await CannabisService(db).destroy(
        tenant_id=user.tenant_id,
        batch_id=data.batch_id,
        grams=data.grams,
        reason=data.reason,
        recorded_by_user_id=user.id,
    )
    return TransactionRead.model_validate(txn)


@router.post(
    "/recall",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def recall(
    data: RecallRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransactionRead:
    txn = await CannabisService(db).recall(
        tenant_id=user.tenant_id,
        batch_id=data.batch_id,
        reason=data.reason,
        recorded_by_user_id=user.id,
    )
    return TransactionRead.model_validate(txn)


@router.get(
    "/unsynced",
    response_model=list[TransactionRead],
    dependencies=[Depends(requires(Permission.AUDIT_VIEW))],
)
async def list_unsynced(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[TransactionRead]:
    rows = await CannabisService(db).unsynced_transactions(tenant_id=user.tenant_id)
    return [TransactionRead.model_validate(r) for r in rows]


@router.post(
    "/transactions/{transaction_id}/mark-synced",
    response_model=TransactionRead,
    dependencies=[Depends(requires(Permission.AUDIT_VIEW))],
)
async def mark_synced(
    transaction_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransactionRead:
    txn = await CannabisService(db).mark_synced(
        tenant_id=user.tenant_id, transaction_id=transaction_id
    )
    return TransactionRead.model_validate(txn)


@router.post(
    "/transactions/{transaction_id}/mark-sync-failed",
    response_model=TransactionRead,
    dependencies=[Depends(requires(Permission.AUDIT_VIEW))],
)
async def mark_sync_failed(
    transaction_id: UUID,
    data: MarkSyncFailedRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TransactionRead:
    txn = await CannabisService(db).mark_sync_failed(
        tenant_id=user.tenant_id, transaction_id=transaction_id, error=data.error
    )
    return TransactionRead.model_validate(txn)
