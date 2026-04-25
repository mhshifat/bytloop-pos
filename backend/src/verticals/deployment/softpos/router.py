from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.deployment.softpos.schemas import (
    ReaderActivityRead,
    RecordTapRequest,
    RegisterReaderRequest,
    SoftposReaderRead,
    SoftposTapEventRead,
)
from src.verticals.deployment.softpos.service import SoftposService

router = APIRouter(prefix="/softpos", tags=["softpos"])


@router.get(
    "/readers",
    response_model=list[SoftposReaderRead],
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def list_readers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SoftposReaderRead]:
    rows = await SoftposService(db).list_readers(tenant_id=user.tenant_id)
    return [SoftposReaderRead.model_validate(r) for r in rows]


@router.post(
    "/readers",
    response_model=SoftposReaderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def register_reader(
    data: RegisterReaderRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SoftposReaderRead:
    reader = await SoftposService(db).register_reader(
        tenant_id=user.tenant_id,
        device_label=data.device_label,
        device_fingerprint=data.device_fingerprint,
    )
    return SoftposReaderRead.model_validate(reader)


@router.post(
    "/readers/{reader_id}/certify",
    response_model=SoftposReaderRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def certify_reader(
    reader_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SoftposReaderRead:
    reader = await SoftposService(db).certify_reader(
        tenant_id=user.tenant_id, reader_id=reader_id
    )
    return SoftposReaderRead.model_validate(reader)


@router.post(
    "/readers/{reader_id}/taps",
    response_model=SoftposTapEventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def record_tap(
    reader_id: UUID,
    data: RecordTapRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SoftposTapEventRead:
    event = await SoftposService(db).record_tap(
        tenant_id=user.tenant_id,
        reader_id=reader_id,
        amount_cents=data.amount_cents,
        card_bin=data.card_bin,
        outcome=data.outcome,
        provider_reference=data.provider_reference,
    )
    return SoftposTapEventRead.model_validate(event)


@router.get(
    "/readers/{reader_id}/activity",
    response_model=ReaderActivityRead,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def reader_activity(
    reader_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> ReaderActivityRead:
    activity = await SoftposService(db).reader_activity(
        tenant_id=user.tenant_id,
        reader_id=reader_id,
        since=since,
        until=until,
    )
    return ReaderActivityRead(
        reader_id=activity.reader_id,
        since=activity.since,
        until=activity.until,
        approved_count=activity.approved_count,
        declined_count=activity.declined_count,
        cancelled_count=activity.cancelled_count,
        error_count=activity.error_count,
        approved_amount_cents=activity.approved_amount_cents,
        events=[SoftposTapEventRead.model_validate(e) for e in activity.events],
    )
