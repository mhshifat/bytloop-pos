from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.audit.entity import AuditEvent
from src.modules.sales.entity import Order, OrderStatus, PaymentMethod
from src.modules.shifts.entity import Shift
from src.verticals.deployment.softpos.entity import SoftposTapEvent, TapOutcome

router = APIRouter(prefix="/ai/risk", tags=["ai", "risk"])


@router.get(
    "/refund-void-abuse",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def refund_void_abuse(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=30, ge=7, le=365),
) -> dict[str, object]:
    """Flag cashiers with anomalous void/refund rates (MVP heuristic)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    # Orders per cashier
    totals = (
        await db.execute(
            select(Order.cashier_id, func.count(Order.id))
            .where(
                Order.tenant_id == user.tenant_id,
                Order.cashier_id.is_not(None),
                Order.closed_at >= start,
            )
            .group_by(Order.cashier_id)
        )
    ).all()
    by_total = {cid: int(c) for cid, c in totals}

    # Voids + refunds from order status.
    voids = (
        await db.execute(
            select(Order.cashier_id, func.count(Order.id))
            .where(
                Order.tenant_id == user.tenant_id,
                Order.cashier_id.is_not(None),
                Order.closed_at >= start,
                Order.status.in_([OrderStatus.VOIDED, OrderStatus.REFUNDED]),
            )
            .group_by(Order.cashier_id)
        )
    ).all()
    by_bad = {cid: int(c) for cid, c in voids}

    rates = []
    for cid, total in by_total.items():
        bad = by_bad.get(cid, 0)
        rate = bad / total if total > 0 else 0.0
        rates.append(rate)
    mean = sum(rates) / len(rates) if rates else 0.0
    var = sum((r - mean) ** 2 for r in rates) / len(rates) if rates else 0.0
    std = var ** 0.5

    items = []
    for cid, total in by_total.items():
        bad = by_bad.get(cid, 0)
        rate = bad / total if total > 0 else 0.0
        z = (rate - mean) / std if std > 1e-9 else 0.0
        if total >= 20 and z >= 2.0:
            items.append(
                {
                    "cashierId": str(cid),
                    "orders": total,
                    "voidOrRefundCount": bad,
                    "voidOrRefundRate": round(rate, 4),
                    "zScore": round(z, 3),
                    "note": "Higher than peer average; review audit log entries for order.voided/order.refunded.",
                }
            )
    items.sort(key=lambda x: x["zScore"], reverse=True)  # type: ignore[arg-type]
    return {"windowDays": days, "peerMean": round(mean, 4), "peerStd": round(std, 4), "items": items}


@router.get(
    "/cash-drawer",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def cash_drawer_discrepancy(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=90, ge=14, le=730),
) -> dict[str, object]:
    """Correlate shift variance patterns by cashier/location (MVP heuristic)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    stmt = (
        select(
            Shift.cashier_id,
            Shift.location_id,
            func.count(Shift.id).label("shifts"),
            func.coalesce(func.avg(Shift.variance_cents), 0).label("avg_var"),
            func.coalesce(func.avg(func.abs(Shift.variance_cents)), 0).label("avg_abs"),
            func.coalesce(func.max(func.abs(Shift.variance_cents)), 0).label("max_abs"),
        )
        .where(
            Shift.tenant_id == user.tenant_id,
            Shift.closed_at.is_not(None),
            Shift.closed_at >= start,
            Shift.variance_cents.is_not(None),
        )
        .group_by(Shift.cashier_id, Shift.location_id)
        .order_by(func.avg(func.abs(Shift.variance_cents)).desc())
        .limit(50)
    )
    rows = (await db.execute(stmt)).all()
    items = [
        {
            "cashierId": str(r.cashier_id),
            "locationId": str(r.location_id),
            "shifts": int(r.shifts),
            "avgVarianceCents": int(r.avg_var),
            "avgAbsVarianceCents": int(r.avg_abs),
            "maxAbsVarianceCents": int(r.max_abs),
            "note": "High average variance can indicate training gaps or fraud; cross-check with order void/refund patterns.",
        }
        for r in rows
    ]
    return {"windowDays": days, "items": items}


@router.get(
    "/softpos/anomalies",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def softpos_anomalies(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    minutes: int = Query(default=60, ge=5, le=1440),
) -> dict[str, object]:
    """Flag SoftPOS tap testing patterns (MVP heuristics).

    - velocity: too many declines per BIN in a short window
    - amount: many low-amount attempts (card testing) or repeated identical amounts
    """
    since = datetime.now(tz=UTC) - timedelta(minutes=minutes)
    stmt = (
        select(SoftposTapEvent)
        .where(SoftposTapEvent.tenant_id == user.tenant_id, SoftposTapEvent.tapped_at >= since)
        .order_by(SoftposTapEvent.tapped_at.desc())
        .limit(2000)
    )
    events = (await db.execute(stmt)).scalars().all()
    if not events:
        return {"windowMinutes": minutes, "items": []}

    by_bin = {}
    for e in events:
        r = by_bin.setdefault(e.card_bin, {"declined": 0, "total": 0, "low_amount": 0, "amounts": {}})
        r["total"] += 1
        if e.outcome == TapOutcome.DECLINED:
            r["declined"] += 1
        if e.amount_cents <= 200:  # $2-ish testing threshold (currency-agnostic MVP)
            r["low_amount"] += 1
        r["amounts"][e.amount_cents] = r["amounts"].get(e.amount_cents, 0) + 1

    items = []
    for card_bin, r in by_bin.items():
        if r["declined"] >= 8 or r["low_amount"] >= 10 or max(r["amounts"].values() or [0]) >= 12:
            items.append(
                {
                    "cardBin": card_bin,
                    "total": r["total"],
                    "declined": r["declined"],
                    "lowAmountAttempts": r["low_amount"],
                    "mostCommonAmountCents": max(r["amounts"], key=r["amounts"].get) if r["amounts"] else None,
                    "mostCommonAmountCount": max(r["amounts"].values() or [0]),
                    "note": "Pattern resembles stolen-card testing or terminal abuse; consider blocking BIN or investigating reader/device.",
                }
            )
    items.sort(key=lambda x: (x["declined"], x["total"]), reverse=True)  # type: ignore[arg-type]
    return {"windowMinutes": minutes, "items": items}

