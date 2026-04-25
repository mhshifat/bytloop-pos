from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from math import log
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy import and_, func, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.modules.discounts.entity import DiscountKind
from src.modules.discounts.schemas import DiscountCreate
from src.modules.discounts.service import DiscountService
from src.modules.sales.entity import Order, OrderItem, OrderStatus
from src.verticals.hospitality.hotel.entity import Reservation, ReservationStatus, Room
from src.verticals.specialty.cinema.entity import Seat, SeatStatus, Show
from src.verticals.specialty.rental.entity import RentalAsset, RentalContract, RentalStatus
from src.verticals.specialty.jewelry.entity import DailyMetalRate
from src.verticals.specialty.jewelry.service import JewelryService

router = APIRouter(prefix="/ai/pricing", tags=["ai", "pricing"])


class HappyHourSuggestion(CamelModel):
    start_hour: int = Field(ge=0, le=23, alias="startHour")
    end_hour: int = Field(ge=1, le=24, alias="endHour")
    percent_off: float = Field(ge=0.01, le=0.8, alias="percentOff")
    reason: str


@router.get(
    "/happy-hour/suggest",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def suggest_happy_hour(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=28, ge=7, le=180),
) -> dict[str, object]:
    """Suggest discount windows for slow hours (MVP heuristic)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    stmt = (
        select(
            func.extract("hour", Order.closed_at).label("hour"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total_cents), 0).label("revenue"),
        )
        .where(
            Order.tenant_id == user.tenant_id,
            Order.status == OrderStatus.COMPLETED,
            Order.closed_at.is_not(None),
            Order.closed_at >= start,
        )
        .group_by(func.extract("hour", Order.closed_at))
    )
    rows = (await db.execute(stmt)).all()
    if not rows:
        return {"suggestions": []}

    by_hour = {int(r.hour): {"orders": int(r.orders), "revenue": int(r.revenue)} for r in rows}
    hours = list(range(24))
    revs = [by_hour.get(h, {"revenue": 0})["revenue"] for h in hours]
    median_rev = sorted(revs)[len(revs) // 2] if revs else 0

    slow = [h for h in hours if by_hour.get(h, {"revenue": 0})["revenue"] <= max(1, int(median_rev * 0.5))]
    suggestions: list[HappyHourSuggestion] = []
    if slow:
        # Choose up to 2 contiguous windows of 2 hours.
        slow.sort()
        windows: list[tuple[int, int]] = []
        i = 0
        while i < len(slow) and len(windows) < 2:
            start_h = slow[i]
            end_h = start_h + 2
            windows.append((start_h, min(24, end_h)))
            i += 2
        for s, e in windows:
            suggestions.append(
                HappyHourSuggestion(
                    startHour=s,
                    endHour=e,
                    percentOff=0.1,
                    reason="Low sales volume during this window over the past weeks.",
                )
            )
    return {"suggestions": [s.model_dump(by_alias=True) for s in suggestions]}


class ApplyHappyHourRequest(CamelModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    start_hour: int = Field(ge=0, le=23, alias="startHour")
    end_hour: int = Field(ge=1, le=24, alias="endHour")
    percent_off: float = Field(ge=0.01, le=0.8, alias="percentOff")
    starts_on: date | None = Field(default=None, alias="startsOn")
    ends_on: date | None = Field(default=None, alias="endsOn")


@router.post(
    "/happy-hour/apply",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def apply_happy_hour(
    req: ApplyHappyHourRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    start_day = req.starts_on or datetime.now(tz=UTC).date()
    end_day = req.ends_on or start_day + timedelta(days=14)
    starts_at = datetime.combine(start_day, time(req.start_hour, 0), tzinfo=UTC)
    ends_at = datetime.combine(end_day, time(req.end_hour % 24, 0), tzinfo=UTC)
    discount = await DiscountService(db).create(
        tenant_id=user.tenant_id,
        data=DiscountCreate(
            code=req.code,
            name=req.name,
            kind=DiscountKind.PERCENT,
            percent=req.percent_off,
            currency="BDT",
            starts_at=starts_at,
            ends_at=ends_at,
        ),
    )
    await db.flush()
    return {"ok": True, "discountId": str(discount.id), "code": discount.code}


@router.get(
    "/elasticity",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def price_elasticity(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=180, ge=30, le=730),
    limit: int = Query(default=30, ge=1, le=200),
) -> dict[str, object]:
    """Estimate price elasticity per product using order_items snapshots (MVP)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    stmt = (
        select(
            OrderItem.product_id,
            func.date_trunc("day", Order.closed_at).label("day"),
            func.sum(OrderItem.quantity).label("qty"),
            func.avg(OrderItem.unit_price_cents).label("avg_price"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            OrderItem.tenant_id == user.tenant_id,
            Order.status == OrderStatus.COMPLETED,
            Order.closed_at >= start,
        )
        .group_by(OrderItem.product_id, func.date_trunc("day", Order.closed_at))
    )
    rows = (await db.execute(stmt)).all()
    by_prod: dict[UUID, list[tuple[float, float]]] = defaultdict(list)
    for pid, _, qty, avg_price in rows:
        q = float(qty or 0)
        p = float(avg_price or 0)
        if q <= 0 or p <= 0:
            continue
        by_prod[pid].append((p, q))

    results: list[dict[str, object]] = []
    for pid, pts in by_prod.items():
        if len(pts) < 12:
            continue
        xs = [log(p) for p, _ in pts]
        ys = [log(q) for _, q in pts]
        n = len(xs)
        xbar = sum(xs) / n
        ybar = sum(ys) / n
        num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
        den = sum((x - xbar) ** 2 for x in xs) or 1e-9
        beta = num / den  # elasticity estimate
        results.append({"productId": str(pid), "elasticity": round(beta, 3), "points": n})

    results.sort(key=lambda r: abs(float(r["elasticity"])), reverse=True)  # type: ignore[arg-type]
    return {"items": results[:limit]}


@router.get(
    "/bundles/suggest",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def bundle_suggest(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=90, ge=14, le=365),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, object]:
    """Suggest bundles using basket co-occurrence (MVP)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    # Pull recent completed orders with their items.
    stmt = (
        select(OrderItem.order_id, OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            OrderItem.tenant_id == user.tenant_id,
            Order.status == OrderStatus.COMPLETED,
            Order.closed_at >= start,
        )
    )
    rows = (await db.execute(stmt)).all()
    by_order: dict[UUID, set[UUID]] = defaultdict(set)
    for oid, pid in rows:
        by_order[oid].add(pid)

    counts: dict[tuple[UUID, UUID], int] = defaultdict(int)
    singles: dict[UUID, int] = defaultdict(int)
    for items in by_order.values():
        ids = sorted(items)
        for a in ids:
            singles[a] += 1
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                counts[(ids[i], ids[j])] += 1

    scored: list[dict[str, object]] = []
    for (a, b), c in counts.items():
        lift = c / max(1, singles[a]) / max(1e-9, (singles[b] / max(1, len(by_order))))
        scored.append({"a": str(a), "b": str(b), "cooccurrence": c, "lift": round(lift, 3)})
    scored.sort(key=lambda r: (r["cooccurrence"], r["lift"]), reverse=True)  # type: ignore[arg-type]
    return {"items": scored[:limit]}


@router.get(
    "/dynamic/suggest",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def dynamic_pricing_suggest(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    """Suggest rate adjustments for hotel/cinema/rental (MVP heuristic)."""
    now = datetime.now(tz=UTC)

    # Hotel occupancy: reservations overlapping next 7 days / room count.
    rooms = (await db.execute(select(Room).where(Room.tenant_id == user.tenant_id))).scalars().all()
    room_count = len(rooms)
    horizon = now.date() + timedelta(days=7)
    resv = (
        await db.execute(
            select(func.count(Reservation.id)).where(
                Reservation.tenant_id == user.tenant_id,
                Reservation.status.in_([ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN]),
                Reservation.check_in < horizon,
                Reservation.check_out > now.date(),
            )
        )
    ).scalar_one()
    occ = (int(resv or 0) / room_count) if room_count > 0 else 0.0
    hotel_delta = 0.0
    if occ > 0.85:
        hotel_delta = 0.12
    elif occ < 0.35:
        hotel_delta = -0.1

    # Cinema utilization: sold seats / total seats for upcoming shows.
    shows = (
        await db.execute(select(Show).where(Show.tenant_id == user.tenant_id, Show.starts_at >= now).limit(20))
    ).scalars().all()
    cinema = []
    for sh in shows:
        total = (
            await db.execute(select(func.count(Seat.id)).where(Seat.show_id == sh.id))
        ).scalar_one()
        sold = (
            await db.execute(
                select(func.count(Seat.id)).where(Seat.show_id == sh.id, Seat.status == SeatStatus.SOLD)
            )
        ).scalar_one()
        util = (int(sold or 0) / int(total or 1)) if total else 0.0
        delta = 0.0
        if util > 0.8:
            delta = 0.08
        elif util < 0.25:
            delta = -0.08
        cinema.append({"showId": str(sh.id), "title": sh.title, "utilization": round(util, 3), "suggestedDeltaPct": delta})

    # Rental utilization: active contracts / assets.
    assets = (await db.execute(select(RentalAsset).where(RentalAsset.tenant_id == user.tenant_id))).scalars().all()
    asset_count = len(assets)
    active = (
        await db.execute(
            select(func.count(RentalContract.id)).where(
                RentalContract.tenant_id == user.tenant_id,
                RentalContract.status.in_([RentalStatus.RESERVED, RentalStatus.OUT]),
                RentalContract.ends_at >= now,
            )
        )
    ).scalar_one()
    util = (int(active or 0) / asset_count) if asset_count > 0 else 0.0
    rental_delta = 0.0
    if util > 0.75:
        rental_delta = 0.1
    elif util < 0.25:
        rental_delta = -0.1

    return {
        "hotel": {"occupancyNext7d": round(occ, 3), "suggestedDeltaPct": hotel_delta},
        "cinema": cinema,
        "rental": {"utilization": round(util, 3), "suggestedDeltaPct": rental_delta},
    }


class ApplyDynamicPricingRequest(CamelModel):
    hotel_delta_pct: float | None = Field(default=None, alias="hotelDeltaPct")
    rental_delta_pct: float | None = Field(default=None, alias="rentalDeltaPct")
    cinema_show_id: UUID | None = Field(default=None, alias="cinemaShowId")
    cinema_delta_pct: float | None = Field(default=None, alias="cinemaDeltaPct")


@router.post(
    "/dynamic/apply",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def dynamic_pricing_apply(
    req: ApplyDynamicPricingRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    updated = 0
    if req.hotel_delta_pct is not None:
        rooms = (await db.execute(select(Room).where(Room.tenant_id == user.tenant_id))).scalars().all()
        for r in rooms:
            r.nightly_rate_cents = max(0, int(round(r.nightly_rate_cents * (1 + req.hotel_delta_pct))))
            updated += 1
    if req.rental_delta_pct is not None:
        assets = (await db.execute(select(RentalAsset).where(RentalAsset.tenant_id == user.tenant_id))).scalars().all()
        for a in assets:
            a.daily_rate_cents = max(0, int(round(a.daily_rate_cents * (1 + req.rental_delta_pct))))
            updated += 1
    if req.cinema_show_id is not None and req.cinema_delta_pct is not None:
        show = await db.get(Show, req.cinema_show_id)
        if show is not None and show.tenant_id == user.tenant_id:
            show.ticket_price_cents = max(0, int(round(show.ticket_price_cents * (1 + req.cinema_delta_pct))))
            updated += 1
    await db.flush()
    return {"ok": True, "updated": updated}


class JewelryRateSuggestRequest(CamelModel):
    metal: str = Field(min_length=1, max_length=16)
    karat: int = Field(ge=1, le=24)
    effective_on: date | None = Field(default=None, alias="effectiveOn")
    spot_per_gram_cents: int = Field(ge=0, alias="spotPerGramCents")
    markup_pct: float = Field(default=0.08, ge=0.0, le=1.0, alias="markupPct")


@router.post(
    "/jewelry/metal-rate/suggest",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def jewelry_rate_suggest(
    req: JewelryRateSuggestRequest,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    suggested = int(round(req.spot_per_gram_cents * (1 + req.markup_pct)))
    return {
        "metal": req.metal,
        "karat": req.karat,
        "effectiveOn": (req.effective_on or datetime.now(tz=UTC).date()).isoformat(),
        "spotPerGramCents": req.spot_per_gram_cents,
        "suggestedRatePerGramCents": suggested,
    }


class JewelryRateApplyRequest(CamelModel):
    metal: str = Field(min_length=1, max_length=16)
    karat: int = Field(ge=1, le=24)
    effective_on: date | None = Field(default=None, alias="effectiveOn")
    rate_per_gram_cents: int = Field(ge=0, alias="ratePerGramCents")


@router.post(
    "/jewelry/metal-rate/apply",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def jewelry_rate_apply(
    req: JewelryRateApplyRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    eff = req.effective_on or datetime.now(tz=UTC).date()
    rate = await JewelryService(db).upsert_rate(
        tenant_id=user.tenant_id,
        metal=req.metal,
        karat=req.karat,
        effective_on=eff,
        rate_per_gram_cents=req.rate_per_gram_cents,
    )
    await db.flush()
    return {"ok": True, "id": str(rate.id)}

