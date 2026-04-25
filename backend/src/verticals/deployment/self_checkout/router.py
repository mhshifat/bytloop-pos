from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.deployment.self_checkout.schemas import (
    CompleteSessionRequest,
    ScanRequest,
    SelfCheckoutScanRead,
    SelfCheckoutSessionRead,
    StartSessionRequest,
)
from src.verticals.deployment.self_checkout.service import SelfCheckoutService

router = APIRouter(prefix="/self-checkout", tags=["self-checkout"])


@router.post(
    "/sessions",
    response_model=SelfCheckoutSessionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def start_session(
    data: StartSessionRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SelfCheckoutSessionRead:
    sess = await SelfCheckoutService(db).start_session(
        tenant_id=user.tenant_id,
        station_label=data.station_label,
        customer_identifier=data.customer_identifier,
    )
    return SelfCheckoutSessionRead.model_validate(sess)


@router.post(
    "/sessions/{session_id}/scans",
    response_model=SelfCheckoutScanRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def scan_item(
    session_id: UUID,
    data: ScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SelfCheckoutScanRead:
    scan = await SelfCheckoutService(db).scan(
        tenant_id=user.tenant_id,
        session_id=session_id,
        barcode=data.barcode,
        quantity=data.quantity,
    )
    return SelfCheckoutScanRead.model_validate(scan)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SelfCheckoutSessionRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def complete_session(
    session_id: UUID,
    data: CompleteSessionRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SelfCheckoutSessionRead:
    sess = await SelfCheckoutService(db).complete_session(
        tenant_id=user.tenant_id,
        session_id=session_id,
        staff_user_id=data.staff_user_id,
    )
    return SelfCheckoutSessionRead.model_validate(sess)


@router.post(
    "/sessions/{session_id}/abandon",
    response_model=SelfCheckoutSessionRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def abandon_session(
    session_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SelfCheckoutSessionRead:
    sess = await SelfCheckoutService(db).abandon_session(
        tenant_id=user.tenant_id, session_id=session_id
    )
    return SelfCheckoutSessionRead.model_validate(sess)


@router.get(
    "/sessions/{session_id}",
    response_model=SelfCheckoutSessionRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_session(
    session_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SelfCheckoutSessionRead:
    sess = await SelfCheckoutService(db).get_session(
        tenant_id=user.tenant_id, session_id=session_id
    )
    return SelfCheckoutSessionRead.model_validate(sess)


@router.get(
    "/sessions/{session_id}/scans",
    response_model=list[SelfCheckoutScanRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_scans(
    session_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SelfCheckoutScanRead]:
    rows = await SelfCheckoutService(db).list_scans(
        tenant_id=user.tenant_id, session_id=session_id
    )
    return [SelfCheckoutScanRead.model_validate(r) for r in rows]
