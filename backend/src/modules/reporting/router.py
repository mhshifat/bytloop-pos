from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.reporting.schemas import (
    DailySalesPoint,
    DashboardSnapshot,
    PaymentMethodPoint,
    SalesSummary,
    TopProductPoint,
)
from src.modules.reporting.service import ReportingService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/dashboard",
    response_model=DashboardSnapshot,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def dashboard(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DashboardSnapshot:
    service = ReportingService(db)
    today = await service.sales_today(tenant_id=user.tenant_id)
    last7 = await service.sales_last_7_days(tenant_id=user.tenant_id)
    customers = await service.customer_count(tenant_id=user.tenant_id)
    low_stock = await service.low_stock_count(tenant_id=user.tenant_id)
    return DashboardSnapshot(
        today=SalesSummary.model_validate(
            {"orderCount": today["orderCount"], "revenueCents": today["revenueCents"]}
        ),
        last7_days=SalesSummary.model_validate(
            {"orderCount": last7["orderCount"], "revenueCents": last7["revenueCents"]}
        ),
        customer_count=customers,
        low_stock_count=low_stock,
    )


@router.get(
    "/sales-by-day",
    response_model=list[DailySalesPoint],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def sales_by_day(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=14, ge=1, le=90),
) -> list[DailySalesPoint]:
    rows = await ReportingService(db).sales_by_day(
        tenant_id=user.tenant_id, days=days
    )
    return [DailySalesPoint.model_validate(r) for r in rows]


@router.get(
    "/top-products",
    response_model=list[TopProductPoint],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def top_products(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[TopProductPoint]:
    rows = await ReportingService(db).top_products(
        tenant_id=user.tenant_id, days=days, limit=limit
    )
    return [TopProductPoint.model_validate(r) for r in rows]


@router.get(
    "/payment-breakdown",
    response_model=list[PaymentMethodPoint],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def payment_breakdown(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=30, ge=1, le=365),
) -> list[PaymentMethodPoint]:
    rows = await ReportingService(db).payment_method_breakdown(
        tenant_id=user.tenant_id, days=days
    )
    return [PaymentMethodPoint.model_validate(r) for r in rows]
