from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import ceil, sqrt
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.modules.catalog.entity import Product
from src.modules.inventory.entity import InventoryLevel, Location, StockMovement, StockMovementKind
from src.modules.procurement.entity import ProductSupplier, PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, Supplier
from src.modules.procurement.schemas import PurchaseOrderCreate, PurchaseOrderItemInput
from src.modules.procurement.service import ProcurementService
from src.modules.audit.api import AuditService
from src.verticals.specialty.pharmacy.entity import PharmacyBatch

router = APIRouter(prefix="/ai/supply-chain", tags=["ai", "supply-chain"])


@router.get(
    "/reorder-points",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def reorder_points(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    location_id: UUID | None = Query(default=None, alias="locationId"),
    days: int = Query(default=60, ge=14, le=365),
    z: float = Query(default=1.65, ge=0.5, le=3.0),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, object]:
    """Dynamic reorder points per (product, location) using demand + lead time variance.

    MVP heuristic:
      ROP = ceil(mean_daily * L + z * std_daily * sqrt(L))
    """
    if location_id is None:
        loc = (
            await db.execute(select(Location).where(Location.tenant_id == user.tenant_id).order_by(Location.created_at))
        ).scalars().first()
        location_id = loc.id if loc else None
    if location_id is None:
        return {"items": []}

    start = datetime.now(tz=UTC) - timedelta(days=days)
    # Pull top movers by sale movements to keep it cheap.
    movers_stmt = (
        select(StockMovement.product_id, func.sum(func.abs(StockMovement.quantity_delta)).label("qty"))
        .where(
            StockMovement.tenant_id == user.tenant_id,
            StockMovement.location_id == location_id,
            StockMovement.kind == StockMovementKind.SALE,
            StockMovement.created_at >= start,
        )
        .group_by(StockMovement.product_id)
        .order_by(func.sum(func.abs(StockMovement.quantity_delta)).desc())
        .limit(limit)
    )
    movers = (await db.execute(movers_stmt)).all()
    if not movers:
        return {"items": []}

    product_ids = [m.product_id for m in movers]
    prods = (
        await db.execute(
            select(Product).where(Product.tenant_id == user.tenant_id, Product.id.in_(product_ids))
        )
    ).scalars().all()
    prod_by = {p.id: p for p in prods}

    # Current inventory levels.
    levels = (
        await db.execute(
            select(InventoryLevel).where(
                InventoryLevel.tenant_id == user.tenant_id,
                InventoryLevel.location_id == location_id,
                InventoryLevel.product_id.in_(product_ids),
            )
        )
    ).scalars().all()
    lvl_by = {l.product_id: l for l in levels}

    # Preferred supplier lead times.
    ps_rows = (
        await db.execute(
            select(ProductSupplier).where(
                ProductSupplier.tenant_id == user.tenant_id,
                ProductSupplier.product_id.in_(product_ids),
                ProductSupplier.is_preferred.is_(True),
            )
        )
    ).scalars().all()
    ps_by = {r.product_id: r for r in ps_rows}

    items: list[dict[str, object]] = []
    for pid in product_ids:
        p = prod_by.get(pid)
        if not p or not p.track_inventory:
            continue
        level = lvl_by.get(pid)
        on_hand = int(level.quantity) if level else 0
        current_rop = int(level.reorder_point) if level else 0
        ps = ps_by.get(pid)
        lead = int(ps.lead_time_days) if ps else 7

        # Mean/std daily demand from sales qty over window (rough).
        qty = 0
        for m in movers:
            if m.product_id == pid:
                qty = int(m.qty or 0)
                break
        mean_daily = qty / max(1, days)
        std_daily = max(0.0, mean_daily * 0.6)  # MVP: approximate variance when we don't have daily buckets
        recommended = int(max(0, ceil(mean_daily * lead + z * std_daily * sqrt(max(1, lead)))))
        items.append(
            {
                "productId": str(pid),
                "sku": p.sku,
                "name": p.name,
                "locationId": str(location_id),
                "onHand": on_hand,
                "currentReorderPoint": current_rop,
                "recommendedReorderPoint": recommended,
                "leadTimeDays": lead,
            }
        )

    return {"items": items}


@router.post(
    "/reorder-points/apply",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def apply_reorder_points(
    payload: dict[str, object],
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    location_id = UUID(str(payload.get("locationId")))
    updates = payload.get("items")
    if not isinstance(updates, list):
        return {"ok": False, "error": "items must be a list"}

    updated = 0
    for row in updates:
        if not isinstance(row, dict):
            continue
        pid = UUID(str(row.get("productId")))
        rop = int(row.get("reorderPoint") or 0)
        lvl = (
            await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.tenant_id == user.tenant_id,
                    InventoryLevel.location_id == location_id,
                    InventoryLevel.product_id == pid,
                )
            )
        ).scalar_one_or_none()
        if lvl is None:
            lvl = InventoryLevel(
                tenant_id=user.tenant_id,
                location_id=location_id,
                product_id=pid,
                quantity=0,
                reorder_point=rop,
            )
            db.add(lvl)
        else:
            lvl.reorder_point = max(0, rop)
        updated += 1

    await AuditService(db).record(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="supply_chain.reorder_points.apply",
        resource_type="inventory",
        resource_id=str(location_id),
        after={"updated": updated},
    )
    await db.flush()
    return {"ok": True, "updated": updated}


@router.post(
    "/purchase-orders/draft-weekly",
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def draft_weekly_purchase_orders(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    location_id: UUID | None = Query(default=None, alias="locationId"),
    days: int = Query(default=60, ge=14, le=365),
) -> dict[str, object]:
    """Generate draft POs per preferred supplier (MVP).

    Requires `product_suppliers` mappings; skips products without preferred supplier.
    """
    rec = await reorder_points(db=db, user=user, location_id=location_id, days=days, z=1.65, limit=200)
    items = rec.get("items") if isinstance(rec, dict) else None
    if not isinstance(items, list):
        return {"purchaseOrdersCreated": 0}

    # Pick items below recommended ROP and map to supplier.
    pids = [UUID(str(i["productId"])) for i in items if isinstance(i, dict)]
    ps_rows = (
        await db.execute(
            select(ProductSupplier).where(
                ProductSupplier.tenant_id == user.tenant_id,
                ProductSupplier.product_id.in_(pids),
                ProductSupplier.is_preferred.is_(True),
            )
        )
    ).scalars().all()
    ps_by = {r.product_id: r for r in ps_rows}

    by_supplier: dict[UUID, list[dict[str, int]]] = {}
    for i in items:
        if not isinstance(i, dict):
            continue
        pid = UUID(str(i["productId"]))
        on_hand = int(i.get("onHand") or 0)
        recommended = int(i.get("recommendedReorderPoint") or 0)
        if on_hand >= recommended:
            continue
        ps = ps_by.get(pid)
        if not ps:
            continue
        need = max(0, recommended - on_hand)
        # Respect pack size and MOQ.
        pack = max(1, int(ps.pack_size))
        moq = max(1, int(ps.min_order_qty))
        qty = max(moq, int(ceil(need / pack) * pack))
        by_supplier.setdefault(ps.supplier_id, []).append(
            {"product_id": pid, "qty": qty, "unit_cost_cents": int(ps.unit_cost_cents)}
        )

    created: list[dict[str, str]] = []
    for supplier_id, lines in by_supplier.items():
        if not lines:
            continue
        po_create = PurchaseOrderCreate(
            supplier_id=supplier_id,
            currency="BDT",
            items=[
                PurchaseOrderItemInput(
                    product_id=l["product_id"],
                    quantity_ordered=l["qty"],
                    unit_cost_cents=l["unit_cost_cents"],
                )
                for l in lines
                if l["qty"] > 0
            ],
        )
        po, _ = await ProcurementService(db).create_purchase_order(
            tenant_id=user.tenant_id, actor_id=user.id, data=po_create
        )
        created.append({"id": str(po.id), "number": po.number, "supplierId": str(po.supplier_id)})
        po.status = PurchaseOrderStatus.DRAFT
    await db.flush()
    return {"purchaseOrdersCreated": len(created), "purchaseOrders": created}


@router.get(
    "/pharmacy/expiry-loss",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def pharmacy_expiry_loss(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    horizon_days: int = Query(default=90, ge=7, le=365, alias="horizonDays"),
) -> dict[str, object]:
    """Predict expiry loss for pharmacy batches (MVP heuristic)."""
    today = datetime.now(tz=UTC).date()
    before = today + timedelta(days=horizon_days)
    batches = (
        await db.execute(
            select(PharmacyBatch).where(
                PharmacyBatch.tenant_id == user.tenant_id,
                PharmacyBatch.expiry_date <= before,
                PharmacyBatch.quantity_remaining > 0,
            )
        )
    ).scalars().all()
    if not batches:
        return {"items": []}

    product_ids = list({b.product_id for b in batches})
    # Demand proxy: last 30d sales quantity per product (across locations).
    start = datetime.now(tz=UTC) - timedelta(days=30)
    demand_stmt = (
        select(StockMovement.product_id, func.sum(func.abs(StockMovement.quantity_delta)).label("qty"))
        .where(
            StockMovement.tenant_id == user.tenant_id,
            StockMovement.kind == StockMovementKind.SALE,
            StockMovement.created_at >= start,
            StockMovement.product_id.in_(product_ids),
        )
        .group_by(StockMovement.product_id)
    )
    demand = {r.product_id: int(r.qty or 0) for r in (await db.execute(demand_stmt)).all()}

    prods = (
        await db.execute(select(Product).where(Product.tenant_id == user.tenant_id, Product.id.in_(product_ids)))
    ).scalars().all()
    prod_by = {p.id: p for p in prods}

    items: list[dict[str, object]] = []
    for b in batches:
        p = prod_by.get(b.product_id)
        if not p:
            continue
        daily = (demand.get(b.product_id, 0) / 30.0) if demand.get(b.product_id, 0) else 0.0
        days_left = max(0, (b.expiry_date - today).days)
        expected_sales = int(daily * days_left)
        predicted_loss = max(0, int(b.quantity_remaining) - expected_sales)
        items.append(
            {
                "batchId": str(b.id),
                "productId": str(b.product_id),
                "sku": p.sku,
                "name": p.name,
                "batchNo": b.batch_no,
                "expiryDate": b.expiry_date.isoformat(),
                "quantityRemaining": int(b.quantity_remaining),
                "expectedSalesBeforeExpiry": expected_sales,
                "predictedExpireUnsold": predicted_loss,
                "suggestion": "Consider FEFO transfer to higher-velocity location or markdown if allowed."
                if predicted_loss > 0
                else "OK",
            }
        )
    items.sort(key=lambda x: (x["expiryDate"], -int(x["predictedExpireUnsold"])))  # type: ignore[arg-type]
    return {"items": items}


@router.get(
    "/suppliers/reliability",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def supplier_reliability(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=180, ge=30, le=730),
) -> dict[str, object]:
    """Score suppliers by on-time receiving vs promise_date (or implied promise)."""
    start = datetime.now(tz=UTC) - timedelta(days=days)
    pos = (
        await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.tenant_id == user.tenant_id,
                PurchaseOrder.created_at >= start,
                PurchaseOrder.status.in_([PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.PARTIALLY_RECEIVED]),
            )
        )
    ).scalars().all()
    if not pos:
        return {"items": []}

    sup_ids = list({p.supplier_id for p in pos})
    sups = (
        await db.execute(select(Supplier).where(Supplier.tenant_id == user.tenant_id, Supplier.id.in_(sup_ids)))
    ).scalars().all()
    sup_by = {s.id: s for s in sups}

    agg: dict[UUID, dict[str, float]] = {}
    for po in pos:
        promise = po.promise_date
        if promise is None and po.sent_at is not None:
            promise = po.sent_at + timedelta(days=7)
        received_at = po.closed_at or datetime.now(tz=UTC)
        on_time = 1.0 if promise is None or received_at <= promise else 0.0
        a = agg.setdefault(po.supplier_id, {"count": 0.0, "on_time": 0.0})
        a["count"] += 1.0
        a["on_time"] += on_time

    items = []
    for sid, a in agg.items():
        s = sup_by.get(sid)
        if not s:
            continue
        count = int(a["count"])
        score = (a["on_time"] / a["count"]) if a["count"] else 0.0
        items.append({"supplierId": str(sid), "name": s.name, "onTimeRate": round(score, 4), "poCount": count})
    items.sort(key=lambda x: (-x["onTimeRate"], -x["poCount"]))  # type: ignore[arg-type]
    return {"items": items}

