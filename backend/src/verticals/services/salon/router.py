from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.salon.schemas import (
    AppointmentCreate,
    AppointmentRead,
    AvailabilityWindow,
    CheckInResponse,
    SalonServiceRead,
    SalonServiceUpsert,
    UpdateAppointmentStatusRequest,
)
from src.verticals.services.salon.service import SalonService

router = APIRouter(prefix="/salon", tags=["salon"])


@router.get(
    "/services",
    response_model=list[SalonServiceRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_services(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SalonServiceRead]:
    rows = await SalonService(db).list_services(tenant_id=user.tenant_id)
    return [SalonServiceRead.model_validate(r) for r in rows]


@router.put(
    "/services",
    response_model=SalonServiceRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_service(
    data: SalonServiceUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SalonServiceRead:
    svc = await SalonService(db).upsert_service(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        duration_minutes=data.duration_minutes,
        price_cents=data.price_cents,
        product_id=data.product_id,
        is_active=data.is_active,
    )
    return SalonServiceRead.model_validate(svc)


@router.get(
    "/appointments",
    response_model=list[AppointmentRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_appointments(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=7, ge=1, le=90),
) -> list[AppointmentRead]:
    now = datetime.utcnow()
    rows = await SalonService(db).list_appointments(
        tenant_id=user.tenant_id, start=now, end=now + timedelta(days=days)
    )
    return [AppointmentRead.model_validate(r) for r in rows]


@router.post(
    "/appointments",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def book_appointment(
    data: AppointmentCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AppointmentRead:
    appt = await SalonService(db).book(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        staff_id=data.staff_id,
        service_id=data.service_id,
        service_name=data.service_name,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
    )
    return AppointmentRead.model_validate(appt)


@router.patch(
    "/appointments/{appointment_id}/status",
    response_model=AppointmentRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_status(
    appointment_id: UUID,
    data: UpdateAppointmentStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AppointmentRead:
    appt = await SalonService(db).update_status(
        tenant_id=user.tenant_id, appointment_id=appointment_id, status=data.status
    )
    return AppointmentRead.model_validate(appt)


@router.get(
    "/stylists/{staff_id}/availability",
    response_model=list[AvailabilityWindow],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def stylist_busy_windows(
    staff_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    date: str = Query(..., description="ISO date (YYYY-MM-DD)"),
) -> list[AvailabilityWindow]:
    day = datetime.fromisoformat(date)
    rows = await SalonService(db).stylist_availability(
        tenant_id=user.tenant_id,
        staff_id=staff_id,
        day_start=day,
        day_end=day + timedelta(days=1),
    )
    return [AvailabilityWindow(starts_at=s, ends_at=e) for s, e in rows]


@router.post(
    "/appointments/{appointment_id}/check-in",
    response_model=CheckInResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def check_in(
    appointment_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CheckInResponse:
    """Flip to CHECKED_IN and return linked product_id so the POS can add it."""
    appt, product_id = await SalonService(db).check_in_to_cart(
        tenant_id=user.tenant_id, appointment_id=appointment_id
    )
    return CheckInResponse(
        appointment=AppointmentRead.model_validate(appt),
        product_id=product_id,
    )
