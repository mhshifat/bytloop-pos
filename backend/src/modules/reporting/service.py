"""Read-only reporting queries.

These run against the live tables for now; heavy rollups should move to
materialized views + Celery Beat refreshes as volume grows (docs/PLAN.md §15b).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.api import Product
from src.modules.customers.api import Customer
from src.modules.inventory.api import InventoryLevel
from src.modules.sales.api import Order, OrderItem, OrderStatus, Payment


class ReportingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sales_today(self, *, tenant_id: UUID) -> dict[str, int]:
        start = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        return await self._sales_between(tenant_id=tenant_id, start=start)

    async def sales_last_7_days(self, *, tenant_id: UUID) -> dict[str, int]:
        start = datetime.now(tz=UTC) - timedelta(days=7)
        return await self._sales_between(tenant_id=tenant_id, start=start)

    async def customer_count(self, *, tenant_id: UUID) -> int:
        stmt = select(func.count(Customer.id)).where(Customer.tenant_id == tenant_id)
        return int((await self._session.execute(stmt)).scalar_one() or 0)

    async def low_stock_count(self, *, tenant_id: UUID) -> int:
        """How many products are currently at/below their reorder point."""
        stmt = select(func.count(InventoryLevel.id)).where(
            InventoryLevel.tenant_id == tenant_id,
            InventoryLevel.reorder_point > 0,
            InventoryLevel.quantity <= InventoryLevel.reorder_point,
        )
        return int((await self._session.execute(stmt)).scalar_one() or 0)

    async def sales_by_day(
        self, *, tenant_id: UUID, days: int = 14
    ) -> list[dict[str, object]]:
        """Daily revenue + order count for the last ``days`` days."""
        start = datetime.now(tz=UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days - 1)
        bucket = func.date_trunc("day", Order.closed_at).label("day")
        stmt = (
            select(
                bucket,
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_cents), 0),
            )
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= start,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "day": day.date().isoformat() if day else "",
                "orderCount": int(order_count or 0),
                "revenueCents": int(revenue or 0),
            }
            for day, order_count, revenue in rows
        ]

    async def top_products(
        self, *, tenant_id: UUID, days: int = 30, limit: int = 10
    ) -> list[dict[str, object]]:
        """Highest-revenue products over the window. Only counts completed orders."""
        start = datetime.now(tz=UTC) - timedelta(days=days)
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
                func.coalesce(func.sum(OrderItem.line_total_cents), 0).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= start,
            )
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(func.sum(OrderItem.line_total_cents).desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "productId": str(pid),
                "name": name,
                "sku": sku,
                "unitsSold": int(units or 0),
                "revenueCents": int(revenue or 0),
            }
            for pid, name, sku, units, revenue in rows
        ]

    async def payment_method_breakdown(
        self, *, tenant_id: UUID, days: int = 30
    ) -> list[dict[str, object]]:
        """How much was taken through each payment method over the window."""
        start = datetime.now(tz=UTC) - timedelta(days=days)
        stmt = (
            select(
                Payment.method,
                func.count(func.distinct(Payment.order_id)),
                func.coalesce(func.sum(Payment.amount_cents), 0),
            )
            .join(Order, Order.id == Payment.order_id)
            .where(
                Payment.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= start,
            )
            .group_by(Payment.method)
            .order_by(func.sum(Payment.amount_cents).desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "method": method.value if hasattr(method, "value") else str(method),
                "orderCount": int(order_count or 0),
                "amountCents": int(amount or 0),
            }
            for method, order_count, amount in rows
        ]

    async def daily_revenue_history(
        self, *, tenant_id: UUID, days: int, product_id: UUID | None = None
    ) -> list[tuple[datetime, int]]:
        """Raw per-day revenue for forecasting/anomaly use. Returns a list
        of (date, revenue_cents) sorted oldest-first. Gaps (days with zero
        orders) are not filled — callers decide how to handle them.
        """
        start = datetime.now(tz=UTC) - timedelta(days=days)
        bucket = func.date_trunc("day", Order.closed_at).label("day")
        if product_id is not None:
            stmt = (
                select(
                    bucket,
                    func.coalesce(func.sum(OrderItem.line_total_cents), 0),
                )
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(
                    Order.tenant_id == tenant_id,
                    Order.status == OrderStatus.COMPLETED,
                    Order.closed_at >= start,
                    OrderItem.product_id == product_id,
                )
                .group_by(bucket)
                .order_by(bucket)
            )
        else:
            stmt = (
                select(
                    bucket,
                    func.coalesce(func.sum(Order.total_cents), 0),
                )
                .where(
                    Order.tenant_id == tenant_id,
                    Order.status == OrderStatus.COMPLETED,
                    Order.closed_at >= start,
                )
                .group_by(bucket)
                .order_by(bucket)
            )
        rows = (await self._session.execute(stmt)).all()
        return [(day, int(rev or 0)) for day, rev in rows if day is not None]

    async def hourly_revenue_history(
        self, *, tenant_id: UUID, days: int
    ) -> list[tuple[datetime, int]]:
        """Per-hour revenue — finer granularity for anomaly detection so we
        can distinguish "quiet morning" from "dead afternoon"."""
        start = datetime.now(tz=UTC) - timedelta(days=days)
        bucket = func.date_trunc("hour", Order.closed_at).label("hour")
        stmt = (
            select(bucket, func.coalesce(func.sum(Order.total_cents), 0))
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= start,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(h, int(rev or 0)) for h, rev in rows if h is not None]

    async def _sales_between(
        self, *, tenant_id: UUID, start: datetime
    ) -> dict[str, int]:
        stmt = select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_cents), 0),
        ).where(
            Order.tenant_id == tenant_id,
            Order.status == OrderStatus.COMPLETED,
            Order.closed_at >= start,
        )
        row = (await self._session.execute(stmt)).one()
        return {
            "orderCount": int(row[0] or 0),
            "revenueCents": int(row[1] or 0),
        }
