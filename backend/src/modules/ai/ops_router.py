from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy import func, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.modules.sales.entity import Order, OrderItem, OrderStatus
from src.verticals.fnb.qsr.entity import DriveThruTicket
from src.verticals.fnb.restaurant.entity import KotTicket, RestaurantTable, TableStatus
from src.verticals.logistics.deliveries.entity import DeliverySchedule, DeliveryStatus
from src.verticals.services.salon.entity import AppointmentStatus, SalonAppointment

router = APIRouter(prefix="/ai/ops", tags=["ai", "ops"])


class ScheduleShift(CamelModel):
    day: date
    start_hour: int = Field(ge=0, le=23, alias="startHour")
    end_hour: int = Field(ge=1, le=24, alias="endHour")
    staff_id: UUID | None = Field(default=None, alias="staffId")
    role_hint: str = Field(default="cashier", alias="roleHint")


@router.get(
    "/staff-schedule/suggest",
    dependencies=[Depends(requires(Permission.STAFF_MANAGE))],
)
async def suggest_staff_schedule(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days_history: int = Query(default=28, ge=7, le=180, alias="daysHistory"),
) -> dict[str, object]:
    """Weekly schedule suggestion (MVP heuristic).

    Uses historical order volume by hour to propose staffing blocks.
    """
    start = datetime.now(tz=UTC) - timedelta(days=days_history)
    stmt = (
        select(func.extract("hour", Order.closed_at).label("hour"), func.count(Order.id).label("orders"))
        .where(
            Order.tenant_id == user.tenant_id,
            Order.status == OrderStatus.COMPLETED,
            Order.closed_at.is_not(None),
            Order.closed_at >= start,
        )
        .group_by(func.extract("hour", Order.closed_at))
    )
    rows = (await db.execute(stmt)).all()
    by_hour = {int(r.hour): int(r.orders or 0) for r in rows}
    peak = max(by_hour.values()) if by_hour else 0

    # Convert demand into staff count per hour (1..4).
    staff_per_hour = {}
    for h in range(24):
        v = by_hour.get(h, 0)
        if peak <= 0:
            staff_per_hour[h] = 1
        else:
            ratio = v / peak
            staff_per_hour[h] = 1 if ratio < 0.25 else 2 if ratio < 0.55 else 3 if ratio < 0.8 else 4

    # Build 7-day schedule template: two shifts covering the day.
    today = datetime.now(tz=UTC).date()
    out: list[ScheduleShift] = []
    for i in range(7):
        d = today + timedelta(days=i)
        # Choose hours based on where demand exists.
        active_hours = [h for h, c in staff_per_hour.items() if c >= 2]
        if not active_hours:
            out.append(ScheduleShift(day=d, startHour=9, endHour=17, staffId=None, roleHint="cashier"))
            continue
        start_h = max(6, min(active_hours))
        end_h = min(23, max(active_hours) + 1)
        out.append(ScheduleShift(day=d, startHour=start_h, endHour=min(24, start_h + 8), staffId=None, roleHint="cashier"))
        if end_h - start_h > 8:
            out.append(ScheduleShift(day=d, startHour=min(24, start_h + 8), endHour=min(24, end_h), staffId=None, roleHint="cashier"))

    return {"shifts": [s.model_dump(by_alias=True) for s in out], "staffPerHour": staff_per_hour}


@router.get(
    "/deliveries/route-optimize",
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def route_optimize(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    day: date = Query(...),
) -> dict[str, object]:
    """Delivery route optimization (MVP): stable ordering without geocoding.

    Sorts by city then postal_code then address_line1.
    """
    start = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
    end = start + timedelta(days=1)
    stmt = (
        select(DeliverySchedule)
        .where(
            DeliverySchedule.tenant_id == user.tenant_id,
            DeliverySchedule.status == DeliveryStatus.SCHEDULED,
            DeliverySchedule.scheduled_for >= start,
            DeliverySchedule.scheduled_for < end,
        )
        .order_by(DeliverySchedule.city, DeliverySchedule.postal_code, DeliverySchedule.address_line1)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "day": day.isoformat(),
        "stops": [
            {
                "deliveryId": str(r.id),
                "orderId": str(r.order_id),
                "city": r.city,
                "postalCode": r.postal_code,
                "addressLine1": r.address_line1,
                "recipientName": r.recipient_name,
                "scheduledFor": r.scheduled_for.isoformat() if r.scheduled_for else None,
            }
            for r in rows
        ],
    }


@router.post(
    "/qsr/prep-time/predict",
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def predict_qsr_prep_time(
    payload: dict[str, str],
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    """Predict prep time and set ticket.estimated_ready_at (MVP heuristic).

    Uses recent KOT prep times as baseline; falls back to 15 minutes.
    """
    ticket_id = UUID(payload["ticketId"])
    ticket = await db.get(DriveThruTicket, ticket_id)
    if ticket is None or ticket.tenant_id != user.tenant_id:
        return {"ok": False, "error": "Ticket not found"}

    # Baseline from kot_tickets: avg ready - fired for last 14d.
    start = datetime.now(tz=UTC) - timedelta(days=14)
    stmt = (
        select(func.avg(func.extract("epoch", KotTicket.ready_at - KotTicket.fired_at)))
        .where(KotTicket.tenant_id == user.tenant_id, KotTicket.ready_at.is_not(None), KotTicket.fired_at >= start)
    )
    avg_seconds = (await db.execute(stmt)).scalar_one()
    base_minutes = int(round((float(avg_seconds) / 60.0))) if avg_seconds else 15
    base_minutes = max(5, min(60, base_minutes))

    eta = datetime.now(tz=UTC) + timedelta(minutes=base_minutes)
    ticket.estimated_ready_at = eta
    await db.flush()
    return {"ok": True, "estimatedReadyAt": eta.isoformat(), "baseMinutes": base_minutes}


@router.get(
    "/restaurant/table-turn",
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def table_turn_forecast(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    """Predict when occupied tables will free (MVP heuristic)."""
    tables = (
        await db.execute(select(RestaurantTable).where(RestaurantTable.tenant_id == user.tenant_id))
    ).scalars().all()
    now = datetime.now(tz=UTC)

    # Use recent completed order durations if possible; fallback to 45m.
    duration_minutes = 45
    start = now - timedelta(days=30)
    # We don't persist table open time; use average KOT ready times as proxy.
    stmt = (
        select(func.avg(func.extract("epoch", KotTicket.ready_at - KotTicket.fired_at)))
        .where(KotTicket.tenant_id == user.tenant_id, KotTicket.ready_at.is_not(None), KotTicket.fired_at >= start)
    )
    avg_seconds = (await db.execute(stmt)).scalar_one()
    if avg_seconds:
        duration_minutes = max(25, min(120, int(round(float(avg_seconds) / 60.0)) + 30))

    out = []
    for t in tables:
        if t.status != TableStatus.OCCUPIED:
            continue
        out.append(
            {
                "tableId": str(t.id),
                "code": t.code,
                "label": t.label,
                "predictedFreeAt": (now + timedelta(minutes=duration_minutes)).isoformat(),
                "confidence": 0.4,
            }
        )
    return {"items": out, "assumedMinutes": duration_minutes}


@router.get(
    "/salon/stylist-match",
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def stylist_match(
    db: DbSession,
    customer_id: UUID = Query(alias="customerId"),
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    """Suggest the best stylist for a customer (MVP heuristic).

    Uses most-frequent historical staff_id for completed appointments.
    """
    stmt = (
        select(SalonAppointment.staff_id, func.count(SalonAppointment.id).label("c"))
        .where(
            SalonAppointment.tenant_id == user.tenant_id,
            SalonAppointment.customer_id == customer_id,
            SalonAppointment.staff_id.is_not(None),
            SalonAppointment.status == AppointmentStatus.COMPLETED,
        )
        .group_by(SalonAppointment.staff_id)
        .order_by(func.count(SalonAppointment.id).desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if not row or row.staff_id is None:
        return {"suggestedStaffId": None, "reason": "No prior stylist history for this customer."}
    return {"suggestedStaffId": str(row.staff_id), "reason": "Based on past completed appointments."}

