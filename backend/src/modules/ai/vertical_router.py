from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.catalog.entity import Product
from src.modules.procurement.entity import ProductSupplier
from src.modules.sales.entity import Order, OrderItem, OrderStatus
from src.verticals.fnb.restaurant.entity import KotStatus, KotTicket
from src.verticals.hospitality.hotel.entity import FolioCharge, Reservation, ReservationStatus, Room
from src.verticals.retail.cannabis.entity import BatchState, CannabisBatch
from src.verticals.services.gym.entity import CheckIn, GymClass, Membership, MembershipStatus
from src.verticals.specialty.rental.entity import RentalContract, RentalStatus

router = APIRouter(prefix="/ai/vertical", tags=["ai", "vertical"])


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    mid = len(ys) // 2
    if len(ys) % 2 == 1:
        return float(ys[mid])
    return float((ys[mid - 1] + ys[mid]) / 2)


@router.get(
    "/menu-engineering",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def menu_engineering(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=60, ge=14, le=365),
) -> dict[str, Any]:
    """BCG-style menu engineering (MVP).

    Popularity: quantity sold vs median.
    Margin: (price - unit_cost) / price using preferred supplier cost where available.
    """
    since = datetime.now(tz=UTC) - timedelta(days=days)

    # Aggregate quantity sold per product in the window.
    sales_rows = (
        await db.execute(
            select(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("qty"),
                func.max(OrderItem.name_snapshot).label("name"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                OrderItem.tenant_id == user.tenant_id,
                Order.tenant_id == user.tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= since,
            )
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(250)
        )
    ).all()
    if not sales_rows:
        return {"windowDays": days, "items": []}

    product_ids = [r.product_id for r in sales_rows]
    products = (
        await db.execute(
            select(Product).where(Product.tenant_id == user.tenant_id, Product.id.in_(product_ids))
        )
    ).scalars().all()
    by_product = {p.id: p for p in products}

    # Prefer the preferred supplier row if present; else min unit cost among suppliers.
    ps_rows = (
        await db.execute(
            select(
                ProductSupplier.product_id,
                func.max(func.cast(ProductSupplier.is_preferred, func.INTEGER)).label("has_pref"),
                func.min(ProductSupplier.unit_cost_cents).label("min_cost"),
                func.max(
                    func.case((ProductSupplier.is_preferred.is_(True), ProductSupplier.unit_cost_cents), else_=None)
                ).label("pref_cost"),
            )
            .where(ProductSupplier.tenant_id == user.tenant_id, ProductSupplier.product_id.in_(product_ids))
            .group_by(ProductSupplier.product_id)
        )
    ).all()
    cost_by_pid: dict[Any, int | None] = {}
    for r in ps_rows:
        cost = int(r.pref_cost) if r.pref_cost is not None else (int(r.min_cost) if r.min_cost is not None else None)
        cost_by_pid[r.product_id] = cost

    pop_values = [float(r.qty or 0) for r in sales_rows]
    pop_med = _median(pop_values)

    margin_pcts: list[float] = []
    margin_by_pid: dict[Any, float | None] = {}
    for r in sales_rows:
        p = by_product.get(r.product_id)
        if p is None or p.price_cents <= 0:
            margin_by_pid[r.product_id] = None
            continue
        unit_cost = cost_by_pid.get(r.product_id)
        if unit_cost is None:
            margin_by_pid[r.product_id] = None
            continue
        mp = max(-1.0, min(1.0, (p.price_cents - unit_cost) / p.price_cents))
        margin_by_pid[r.product_id] = float(mp)
        margin_pcts.append(float(mp))
    margin_med = _median(margin_pcts)

    items = []
    for r in sales_rows:
        p = by_product.get(r.product_id)
        if p is None:
            continue
        qty = float(r.qty or 0)
        pop = "high" if qty >= pop_med else "low"
        mp = margin_by_pid.get(r.product_id)
        if mp is None:
            quadrant = "unknown"
        else:
            margin = "high" if mp >= margin_med else "low"
            if pop == "high" and margin == "high":
                quadrant = "star"
            elif pop == "high" and margin == "low":
                quadrant = "plowhorse"
            elif pop == "low" and margin == "high":
                quadrant = "puzzle"
            else:
                quadrant = "dog"
        action = {
            "star": "Promote and protect availability; consider small price lift.",
            "plowhorse": "Consider modest price increase or cost reduction; keep prominent placement.",
            "puzzle": "Improve visibility / rename / reposition; test promos to raise volume.",
            "dog": "Consider removing, shrinking menu space, or bundling to move inventory.",
            "unknown": "Add supplier unit cost mapping to compute margins.",
        }[quadrant]
        items.append(
            {
                "productId": str(p.id),
                "name": r.name or p.name,
                "qtySold": int(qty),
                "priceCents": int(p.price_cents),
                "unitCostCents": cost_by_pid.get(r.product_id),
                "marginPct": round(float(mp), 4) if mp is not None else None,
                "classification": quadrant,
                "recommendation": action,
            }
        )

    return {
        "windowDays": days,
        "popularityMedianQty": round(pop_med, 3),
        "marginMedianPct": round(margin_med, 4),
        "items": items,
    }


@router.get(
    "/restaurant/wait-time",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def restaurant_wait_time(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    station: str | None = Query(default=None),
) -> dict[str, Any]:
    """Estimate 'ready in X minutes' using recent prep times + current KDS backlog (MVP)."""
    now = datetime.now(tz=UTC)
    hist_since = now - timedelta(days=7)
    backlog_since = now - timedelta(hours=6)

    stmt = select(KotTicket).where(KotTicket.tenant_id == user.tenant_id)
    if station:
        stmt = stmt.where(KotTicket.station == station)

    hist = (
        await db.execute(
            stmt.where(
                KotTicket.ready_at.is_not(None),
                KotTicket.fired_at >= hist_since,
            )
        )
    ).scalars().all()

    prep_minutes: list[float] = []
    for t in hist:
        if t.ready_at is None:
            continue
        delta = (t.ready_at - t.fired_at).total_seconds() / 60.0
        if 0 <= delta <= 180:
            prep_minutes.append(delta)
    base = _median(prep_minutes) if prep_minutes else 15.0

    backlog = (
        await db.execute(
            stmt.where(
                KotTicket.fired_at >= backlog_since,
                KotTicket.status.in_([KotStatus.NEW, KotStatus.PREPARING]),
            )
        )
    ).scalars().all()
    backlog_count = len(backlog)
    eta = base + (0.9 * backlog_count)
    eta = max(3.0, min(120.0, float(eta)))

    return {
        "station": station,
        "basePrepMinutesMedian": round(float(base), 2),
        "backlogTickets": backlog_count,
        "estimatedReadyInMinutes": int(round(eta)),
        "note": "MVP heuristic: recent median prep time + backlog factor. Improve later with per-station regression and item counts.",
    }


@router.get(
    "/cannabis/potency-price-match",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def cannabis_potency_price_match(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    desired_thc_pct: float = Query(alias="desiredThcPct", default=18.0, ge=0, le=60),
    desired_cbd_pct: float = Query(alias="desiredCbdPct", default=0.0, ge=0, le=60),
    max_price_cents: int | None = Query(alias="maxPriceCents", default=None, ge=0),
    limit: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    """Recommend strains/batches by potency closeness + price (MVP)."""
    batches = (
        await db.execute(
            select(CannabisBatch, Product)
            .join(Product, Product.id == CannabisBatch.product_id)
            .where(
                CannabisBatch.tenant_id == user.tenant_id,
                Product.tenant_id == user.tenant_id,
                CannabisBatch.state.in_([BatchState.ACTIVE, BatchState.RECEIVED]),
                CannabisBatch.quantity_grams > 0,
            )
        )
    ).all()

    scored = []
    for b, p in batches:
        price = int(p.price_cents or 0)
        if max_price_cents is not None and price > max_price_cents:
            continue
        thc = float(b.thc_pct or 0)
        cbd = float(b.cbd_pct or 0)
        potency_dist = abs(thc - desired_thc_pct) + (0.5 * abs(cbd - desired_cbd_pct))
        # Penalize higher prices slightly so equal potency prefers cheaper.
        score = potency_dist + (price / 20000.0)
        scored.append((score, b, p))
    scored.sort(key=lambda x: x[0])
    top = scored[:limit]

    return {
        "query": {
            "desiredThcPct": desired_thc_pct,
            "desiredCbdPct": desired_cbd_pct,
            "maxPriceCents": max_price_cents,
        },
        "items": [
            {
                "batchId": str(b.id),
                "strainName": b.strain_name,
                "thcPct": float(b.thc_pct or 0),
                "cbdPct": float(b.cbd_pct or 0),
                "quantityGrams": float(b.quantity_grams),
                "productId": str(p.id),
                "productName": p.name,
                "priceCents": int(p.price_cents),
                "score": round(float(score), 4),
                "note": "MVP matcher: potency closeness + light price penalty. Extend later with 'effects' tags in batch vertical_data.",
            }
            for score, b, p in top
        ],
    }


@router.get(
    "/hotel/upsell",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def hotel_upsell_prediction(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    for_date: date | None = Query(alias="forDate", default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    """Predict which guests might accept upgrades at check-in (MVP heuristic)."""
    d = for_date or date.today()

    # Reservations checking in that day.
    resvs = (
        await db.execute(
            select(Reservation)
            .where(
                Reservation.tenant_id == user.tenant_id,
                Reservation.status == ReservationStatus.BOOKED,
                Reservation.check_in == d,
            )
            .order_by(Reservation.check_in)
            .limit(limit)
        )
    ).scalars().all()
    if not resvs:
        return {"forDate": d.isoformat(), "items": []}

    # Prior incidentals per customer (proxy for willingness to spend).
    customer_ids = list({r.customer_id for r in resvs})
    charges = (
        await db.execute(
            select(FolioCharge.reservation_id, FolioCharge.amount_cents)
            .join(Reservation, Reservation.id == FolioCharge.reservation_id)
            .where(
                FolioCharge.tenant_id == user.tenant_id,
                Reservation.tenant_id == user.tenant_id,
                Reservation.customer_id.in_(customer_ids),
            )
        )
    ).all()
    incidental_by_customer: dict[Any, int] = {cid: 0 for cid in customer_ids}
    # Map reservation->customer for aggregation
    resv_to_customer = {r.id: r.customer_id for r in resvs}
    for resv_id, amt in charges:
        cid = resv_to_customer.get(resv_id)
        if cid is not None:
            incidental_by_customer[cid] = incidental_by_customer.get(cid, 0) + int(amt or 0)

    # Room categories/rates for potential upgrade delta.
    rooms = (
        await db.execute(select(Room).where(Room.tenant_id == user.tenant_id))
    ).scalars().all()
    categories = sorted({r.category for r in rooms})
    cat_max_rate = {}
    for r in rooms:
        cat_max_rate[r.category] = max(int(r.nightly_rate_cents), int(cat_max_rate.get(r.category, 0)))

    items = []
    for r in resvs:
        spend = incidental_by_customer.get(r.customer_id, 0)
        nights = max(1, (r.check_out - r.check_in).days)
        spend_per_night = spend / nights
        score = 0.0
        score += min(1.5, spend_per_night / 5000.0)  # scaled
        score += min(0.5, nights / 5.0)

        items.append(
            {
                "reservationId": str(r.id),
                "customerId": str(r.customer_id),
                "nights": nights,
                "historicalIncidentalsCents": int(spend),
                "score": round(float(score), 3),
                "suggestion": "Offer a room upgrade or package add-on at check-in." if score >= 1.0 else "Standard check-in; low upsell likelihood.",
                "note": f"MVP score based on past folio incidentals (proxy for willingness to spend). Categories available: {categories}",
            }
        )
    items.sort(key=lambda x: x["score"], reverse=True)  # type: ignore[arg-type]
    return {"forDate": d.isoformat(), "items": items}


@router.get(
    "/rental/damage-risk",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def rental_damage_risk(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """Score customers by past rental returns (late/damage fees) and suggest deposit multiplier (MVP)."""
    rows = (
        await db.execute(
            select(
                RentalContract.customer_id,
                func.count(RentalContract.id).label("contracts"),
                func.sum(RentalContract.damage_fee_cents).label("damage"),
                func.sum(RentalContract.late_fee_cents).label("late"),
                func.sum(func.case((RentalContract.damage_fee_cents > 0, 1), else_=0)).label("damage_count"),
            )
            .where(
                RentalContract.tenant_id == user.tenant_id,
                RentalContract.status.in_([RentalStatus.RETURNED, RentalStatus.OVERDUE]),
            )
            .group_by(RentalContract.customer_id)
            .order_by(func.sum(RentalContract.damage_fee_cents).desc())
            .limit(limit)
        )
    ).all()

    items = []
    for r in rows:
        contracts = int(r.contracts or 0)
        damage = int(r.damage or 0)
        late = int(r.late or 0)
        damage_count = int(r.damage_count or 0)
        damage_rate = (damage_count / contracts) if contracts else 0.0
        avg_fee = (damage + late) / contracts if contracts else 0.0
        score = min(2.0, (1.2 * damage_rate) + (avg_fee / 5000.0))
        multiplier = 1.0
        if score >= 1.3:
            multiplier = 1.75
        elif score >= 0.8:
            multiplier = 1.25
        items.append(
            {
                "customerId": str(r.customer_id),
                "contracts": contracts,
                "damageFeesCents": damage,
                "lateFeesCents": late,
                "damageRate": round(damage_rate, 3),
                "score": round(float(score), 3),
                "recommendedDepositMultiplier": multiplier,
                "note": "MVP: based on prior contracts with damage/late fees. Extend later with asset types, notes embeddings, and chargeback history.",
            }
        )
    items.sort(key=lambda x: x["score"], reverse=True)  # type: ignore[arg-type]
    return {"items": items}


@router.get(
    "/gym/churn-nudges",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def gym_churn_nudges(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=14, ge=7, le=60),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """Detect check-in frequency drop and suggest outreach + classes (MVP)."""
    now = datetime.now(tz=UTC)
    w = timedelta(days=days)
    recent_since = now - w
    prev_since = now - (2 * w)

    members = (
        await db.execute(
            select(Membership)
            .where(
                Membership.tenant_id == user.tenant_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Membership.ends_on)
            .limit(limit)
        )
    ).scalars().all()
    if not members:
        return {"windowDays": days, "items": []}

    mids = [m.id for m in members]
    counts = (
        await db.execute(
            select(
                CheckIn.membership_id,
                func.sum(func.case((CheckIn.checked_in_at >= recent_since, 1), else_=0)).label("recent"),
                func.sum(func.case((func.and_(CheckIn.checked_in_at >= prev_since, CheckIn.checked_in_at < recent_since), 1), else_=0)).label("prev"),
            )
            .where(CheckIn.tenant_id == user.tenant_id, CheckIn.membership_id.in_(mids), CheckIn.checked_in_at >= prev_since)
            .group_by(CheckIn.membership_id)
        )
    ).all()
    by_mid = {r.membership_id: (int(r.recent or 0), int(r.prev or 0)) for r in counts}

    upcoming = (
        await db.execute(
            select(GymClass)
            .where(GymClass.tenant_id == user.tenant_id, GymClass.starts_at >= now)
            .order_by(GymClass.starts_at)
            .limit(5)
        )
    ).scalars().all()
    class_summaries = [
        {"classId": str(c.id), "title": c.title, "startsAt": c.starts_at.isoformat()}
        for c in upcoming
    ]

    items = []
    for m in members:
        recent, prev = by_mid.get(m.id, (0, 0))
        if prev >= 2 and recent <= max(0, int(round(prev * 0.5))):
            drop_pct = 1.0 - (recent / prev) if prev else 0.0
            msg = (
                "We noticed your visits have dipped — want a class recommendation or a trainer check-in?"
                if drop_pct >= 0.5
                else "Quick nudge: book a class this week to stay on track."
            )
            items.append(
                {
                    "membershipId": str(m.id),
                    "customerId": str(m.customer_id),
                    "recentCheckins": recent,
                    "previousCheckins": prev,
                    "dropPct": round(float(drop_pct), 3),
                    "suggestedMessage": msg,
                    "suggestedClasses": class_summaries,
                }
            )
    items.sort(key=lambda x: x["dropPct"], reverse=True)  # type: ignore[arg-type]
    return {"windowDays": days, "items": items}

