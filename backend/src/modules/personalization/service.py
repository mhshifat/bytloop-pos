from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.core import cache
from src.modules.catalog.entity import Product
from src.modules.ai.service import AIAnalyticsService
from src.modules.customers.entity import Customer
from src.modules.personalization.entity import CampaignDelivery, CampaignTrigger, CustomerSegment, SegmentMembership
from src.modules.sales.entity import Order, OrderItem, OrderStatus
from src.integrations.ai.base import Message
from src.integrations.ai.factory import get_ai_adapter


class PersonalizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Segments
    async def list_segments(self, *, tenant_id: UUID) -> list[CustomerSegment]:
        stmt = select(CustomerSegment).where(CustomerSegment.tenant_id == tenant_id).order_by(
            CustomerSegment.created_at.desc()
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_segment_members(
        self, *, tenant_id: UUID, segment_id: UUID, limit: int = 200
    ) -> list[SegmentMembership]:
        seg = (
            await self._session.execute(
                select(CustomerSegment).where(
                    CustomerSegment.id == segment_id, CustomerSegment.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if seg is None:
            raise NotFoundError("Segment not found.")
        stmt = (
            select(SegmentMembership)
            .where(SegmentMembership.tenant_id == tenant_id, SegmentMembership.segment_id == segment_id)
            .order_by(SegmentMembership.score.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def recompute_segments(self, *, tenant_id: UUID) -> tuple[int, int]:
        """Auto-segment customers using simple clustering over RFM features.

        Writes N cluster segments plus one rule-based churn-risk segment.
        """
        # Clear memberships for this tenant; keep historical segments table tidy by replacing cluster segments.
        await self._session.execute(delete(SegmentMembership).where(SegmentMembership.tenant_id == tenant_id))
        await self._session.execute(
            delete(CustomerSegment).where(
                CustomerSegment.tenant_id == tenant_id, CustomerSegment.kind == "cluster_auto"
            )
        )

        # Build RFM features per customer.
        now = datetime.now(tz=UTC)
        stmt = (
            select(
                Customer.id.label("customer_id"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_cents), 0).label("total_spent_cents"),
                func.max(Order.closed_at).label("last_order_at"),
            )
            .select_from(Customer)
            .join(Order, Order.customer_id == Customer.id, isouter=True)
            .where(Customer.tenant_id == tenant_id)
            .where((Order.status == OrderStatus.COMPLETED) | (Order.id.is_(None)))
            .group_by(Customer.id)
        )
        rows = (await self._session.execute(stmt)).all()
        feats: list[dict[str, Any]] = []
        for cid, order_count, total_spent, last_order_at in rows:
            oc = int(order_count or 0)
            ts = int(total_spent or 0)
            days_since_last = 10_000
            if last_order_at is not None:
                days_since_last = max(0, int((now - last_order_at).total_seconds() // 86400))
            avg_order = int(ts / oc) if oc > 0 else 0
            feats.append(
                {
                    "customer_id": cid,
                    "order_count": oc,
                    "total_spent_cents": ts,
                    "days_since_last": days_since_last,
                    "avg_order_cents": avg_order,
                }
            )

        memberships_written = 0
        segments_created = 0

        # Rule-based churn segment (reuse existing churn logic).
        churn = await AIAnalyticsService(self._session).customers_at_churn_risk(tenant_id=tenant_id, threshold=0.6)
        churn_seg = CustomerSegment(
            tenant_id=tenant_id, name="Likely to churn", kind="rule", definition={"source": "ai.churn", "threshold": 0.6}
        )
        self._session.add(churn_seg)
        await self._session.flush()
        segments_created += 1
        for row in churn[:500]:
            self._session.add(
                SegmentMembership(
                    tenant_id=tenant_id,
                    segment_id=churn_seg.id,
                    customer_id=row["customer_id"],
                    score=float(row.get("churn_probability") or 0.0),
                    meta={"days_since_last": row.get("days_since_last"), "order_count": row.get("order_count")},
                )
            )
            memberships_written += 1

        # Cluster customers (if enough data) into 3 groups.
        trainable = [f for f in feats if f["order_count"] > 0]
        k = 3 if len(trainable) >= 30 else 0
        if k > 0:
            try:
                from sklearn.cluster import KMeans  # noqa: PLC0415

                X = [
                    [f["order_count"], f["days_since_last"], f["avg_order_cents"], f["total_spent_cents"]]
                    for f in trainable
                ]
                km = KMeans(n_clusters=k, n_init=10, random_state=42)
                labels = km.fit_predict(X).tolist()
            except Exception:  # noqa: BLE001
                labels = []
                k = 0

            if k > 0 and labels:
                # Optionally auto-name clusters with Groq.
                adapter = get_ai_adapter()
                cluster_names = [f"Segment {i+1}" for i in range(k)]
                if adapter.is_enabled():
                    schema = {
                        "type": "object",
                        "properties": {
                            "names": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["names"],
                    }
                    # Summarize each cluster with simple stats for naming.
                    summaries: list[dict[str, Any]] = []
                    for i in range(k):
                        members = [f for f, lab in zip(trainable, labels) if lab == i]
                        if not members:
                            summaries.append({"i": i, "size": 0})
                            continue
                        summaries.append(
                            {
                                "i": i,
                                "size": len(members),
                                "avg_orders": round(sum(m["order_count"] for m in members) / len(members), 2),
                                "avg_days_since_last": round(sum(m["days_since_last"] for m in members) / len(members), 2),
                                "avg_total_spent_cents": int(sum(m["total_spent_cents"] for m in members) / len(members)),
                            }
                        )
                    prompt = (
                        "Name customer segments based on behavior summaries.\n"
                        "Return JSON { names: string[] } with exactly "
                        f"{k} short names (3-5 words each).\n"
                        f"Summaries: {summaries}"
                    )
                    try:
                        named = await adapter.structured(
                            messages=[Message(role="system", content=prompt)],
                            json_schema=schema,
                            temperature=0.3,
                            max_tokens=200,
                        )
                        names = named.get("names")
                        if isinstance(names, list) and len(names) == k:
                            cluster_names = [str(n)[:40] for n in names]
                    except Exception:  # noqa: BLE001
                        pass

                # Create segments + memberships.
                seg_by_label: dict[int, CustomerSegment] = {}
                for i in range(k):
                    seg = CustomerSegment(
                        tenant_id=tenant_id,
                        name=cluster_names[i],
                        kind="cluster_auto",
                        definition={"k": k, "label": i},
                    )
                    self._session.add(seg)
                    await self._session.flush()
                    seg_by_label[i] = seg
                    segments_created += 1

                for f, lab in zip(trainable, labels):
                    seg = seg_by_label.get(int(lab))
                    if not seg:
                        continue
                    score = float(f["total_spent_cents"])
                    self._session.add(
                        SegmentMembership(
                            tenant_id=tenant_id,
                            segment_id=seg.id,
                            customer_id=f["customer_id"],
                            score=score,
                            meta={
                                "order_count": f["order_count"],
                                "days_since_last": f["days_since_last"],
                                "avg_order_cents": f["avg_order_cents"],
                                "total_spent_cents": f["total_spent_cents"],
                            },
                        )
                    )
                    memberships_written += 1

        await self._session.flush()
        return segments_created, memberships_written

    # Campaign triggers
    async def list_triggers(self, *, tenant_id: UUID) -> list[CampaignTrigger]:
        stmt = select(CampaignTrigger).where(CampaignTrigger.tenant_id == tenant_id).order_by(
            CampaignTrigger.created_at.desc()
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def upsert_trigger(
        self,
        *,
        tenant_id: UUID,
        trigger_id: UUID | None,
        data: dict[str, Any],
    ) -> CampaignTrigger:
        row: CampaignTrigger | None = None
        if trigger_id is not None:
            row = (
                await self._session.execute(
                    select(CampaignTrigger).where(
                        CampaignTrigger.id == trigger_id, CampaignTrigger.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none()
        if row is None:
            row = CampaignTrigger(tenant_id=tenant_id)
            self._session.add(row)

        for k in (
            "segment_id",
            "threshold",
            "subject",
            "html_template",
            "discount_code",
            "cooldown_days",
            "enabled",
        ):
            if k in data:
                setattr(row, k, data[k])
        await self._session.flush()
        return row

    async def can_send_to_customer(
        self, *, tenant_id: UUID, trigger_id: UUID, customer_id: UUID
    ) -> bool:
        trig = (
            await self._session.execute(
                select(CampaignTrigger).where(
                    CampaignTrigger.id == trigger_id, CampaignTrigger.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if trig is None or not trig.enabled:
            return False
        log = (
            await self._session.execute(
                select(CampaignDelivery).where(
                    CampaignDelivery.tenant_id == tenant_id,
                    CampaignDelivery.trigger_id == trigger_id,
                    CampaignDelivery.customer_id == customer_id,
                )
            )
        ).scalar_one_or_none()
        if log is None:
            return True
        return log.last_sent_at <= datetime.now(tz=UTC) - timedelta(days=int(trig.cooldown_days))

    async def next_best_offers(
        self, *, tenant_id: UUID, product_id: UUID, limit: int = 5, days: int = 90
    ) -> list[dict[str, object]]:
        """Item-to-item co-occurrence: 'bought with X' → top Y products."""
        cache_key = f"pos:p13n:nbo:{tenant_id}:{product_id}:{limit}:{days}"
        cached = await cache.get_str(cache_key)
        if cached:
            try:
                import json  # noqa: PLC0415

                data = json.loads(cached)
                if isinstance(data, list):
                    return data
            except Exception:  # noqa: BLE001
                pass

        start = datetime.now(tz=UTC) - timedelta(days=days)
        # Find co-occurring products within the same completed order.
        oi1 = OrderItem.__table__.alias("oi1")
        oi2 = OrderItem.__table__.alias("oi2")
        stmt = (
            select(
                oi2.c.product_id.label("product_id"),
                func.count().label("count"),
            )
            .select_from(oi1)
            .join(Order, Order.id == oi1.c.order_id)
            .join(oi2, oi2.c.order_id == oi1.c.order_id)
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= start,
                oi1.c.product_id == product_id,
                oi2.c.product_id != product_id,
            )
            .group_by(oi2.c.product_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        if not rows:
            return []

        pids = [r.product_id for r in rows]
        prod_rows = (
            await self._session.execute(
                select(Product).where(Product.tenant_id == tenant_id, Product.id.in_(pids))
            )
        ).scalars().all()
        by_id = {p.id: p for p in prod_rows}

        out: list[dict[str, object]] = []
        for r in rows:
            p = by_id.get(r.product_id)
            if not p:
                continue
            out.append(
                {
                    "productId": str(p.id),
                    "name": p.name,
                    "sku": p.sku,
                    "priceCents": p.price_cents,
                    "currency": p.currency,
                    "score": int(r.count),
                }
            )

        await cache.set_str(cache_key, __import__("json").dumps(out), ttl_seconds=60 * 10)
        return out

