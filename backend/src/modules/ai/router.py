"""AI-analytics HTTP endpoints.

Mounted under /ai/reports/* so the existing /reports/* namespace stays
lean for the non-AI analytics. All endpoints require REPORTS_VIEW.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import ValidationError
from src.core.permissions import Permission
from src.integrations.ai.base import AIUnavailableError
from src.modules.ai.service import AIAnalyticsService
from src.modules.reporting.schemas import (
    AnomalyPoint,
    AnomalyReport,
    AttributionChannel,
    AttributionReport,
    BenchmarkPoint,
    BenchmarkReport,
    ChurnReport,
    ChurnRiskCustomer,
    CohortCell,
    CohortReport,
    ForecastPoint,
    ForecastResult,
    LifetimeValuePrediction,
    NLAnswer,
    NLQuestion,
)

router = APIRouter(prefix="/ai/reports", tags=["ai-reports"])


@router.get(
    "/forecast",
    response_model=ForecastResult,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def forecast(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    horizon_days: int = Query(default=14, ge=1, le=90),
    history_days: int = Query(default=90, ge=7, le=365),
    product_id: UUID | None = Query(default=None),
    method: str = Query(
        default="seasonal_naive",
        pattern="^(seasonal_naive|prophet)$",
        description="seasonal_naive (fast default) or prophet (optional extra)",
    ),
) -> ForecastResult:
    pts = await AIAnalyticsService(db).forecast_revenue(
        tenant_id=user.tenant_id,
        horizon_days=horizon_days,
        history_days=history_days,
        product_id=product_id,
        method=method,
    )
    return ForecastResult(
        horizon_days=horizon_days,
        generated_at=datetime.now(tz=UTC).isoformat(),
        product_id=str(product_id) if product_id else None,
        points=[
            ForecastPoint(day=d.isoformat(), forecast_revenue_cents=v)
            for d, v in pts
        ],
    )


@router.get(
    "/forecast/accuracy",
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def forecast_accuracy(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    holdout_days: int = Query(default=7, ge=1, le=30),
    history_days: int = Query(default=120, ge=30, le=365),
) -> dict[str, float | None]:
    """MAPE per forecaster for A/B evaluation. Run this before switching
    a tenant's default method to ``prophet``."""
    return await AIAnalyticsService(db).evaluate_forecasters(
        tenant_id=user.tenant_id,
        holdout_days=holdout_days,
        history_days=history_days,
    )


@router.get(
    "/anomalies",
    response_model=AnomalyReport,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def anomalies(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    window_days: int = Query(default=60, ge=7, le=180),
) -> AnomalyReport:
    rows = await AIAnalyticsService(db).detect_demand_anomalies(
        tenant_id=user.tenant_id, window_days=window_days
    )
    return AnomalyReport(
        window_days=window_days,
        anomalies=[
            AnomalyPoint(
                timestamp=ts.isoformat(),
                revenue_cents=v,
                severity=round(sev, 3),
            )
            for ts, v, sev in rows
        ],
    )


@router.get(
    "/churn-risk",
    response_model=ChurnReport,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def churn_risk(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    threshold: float = Query(default=0.6, ge=0.0, le=1.0),
) -> ChurnReport:
    rows = await AIAnalyticsService(db).customers_at_churn_risk(
        tenant_id=user.tenant_id, threshold=threshold
    )
    return ChurnReport(
        threshold=threshold,
        customers=[
            ChurnRiskCustomer(
                customer_id=str(r["customer_id"]),
                email=r.get("email"),
                first_name=r["first_name"],
                last_name=r["last_name"],
                days_since_last_order=r["days_since_last"],
                order_count=r["order_count"],
                total_spent_cents=r["total_spent_cents"],
                churn_probability=round(r["churn_probability"], 3),
            )
            for r in rows
        ],
    )


@router.get(
    "/customers/{customer_id}/ltv",
    response_model=LifetimeValuePrediction,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def lifetime_value(
    customer_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LifetimeValuePrediction:
    result = await AIAnalyticsService(db).predict_ltv(
        tenant_id=user.tenant_id, customer_id=customer_id
    )
    return LifetimeValuePrediction(
        customer_id=result["customer_id"],
        predicted_12mo_cents=result["predicted_12mo_cents"],
        past_12mo_cents=result["past_12mo_cents"],
        confidence=round(result["confidence"], 3),
    )


@router.post(
    "/ask",
    response_model=NLAnswer,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def ask(
    req: NLQuestion,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> NLAnswer:
    question = (req.question or "").strip()
    if not question:
        raise ValidationError("Question cannot be empty.")
    if len(question) > 2000:
        raise ValidationError("Question is too long (max 2000 chars).")
    try:
        result = await AIAnalyticsService(db).answer_question(
            tenant_id=user.tenant_id, question=question
        )
    except AIUnavailableError as exc:
        # Surface the provider state to the UI so it can render a useful
        # fallback (e.g. "AI reporting not configured").
        return NLAnswer(
            question=question,
            answer=f"AI reporting is unavailable: {exc}",
            rows=[],
            sql=None,
        )
    return NLAnswer(**result)


@router.get(
    "/cohort-retention",
    response_model=CohortReport,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def cohort_retention(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    months_back: int = Query(default=12, ge=3, le=36),
) -> CohortReport:
    result = await AIAnalyticsService(db).cohort_retention(
        tenant_id=user.tenant_id, months_back=months_back
    )
    return CohortReport(
        cells=[CohortCell(**c) for c in result["cells"]],
        insight=result["insight"],
    )


@router.get(
    "/benchmark",
    response_model=BenchmarkReport,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def benchmark(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BenchmarkReport:
    result = await AIAnalyticsService(db).benchmark_against_peers(
        tenant_id=user.tenant_id
    )
    return BenchmarkReport(
        vertical=result["vertical"],
        points=[BenchmarkPoint(**p) for p in result["points"]],
        insight=result["insight"],
    )


@router.get(
    "/attribution",
    response_model=AttributionReport,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def attribution(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    window_days: int = Query(default=30, ge=7, le=180),
) -> AttributionReport:
    result = await AIAnalyticsService(db).attribution_report(
        tenant_id=user.tenant_id, window_days=window_days
    )
    return AttributionReport(
        window_days=result["window_days"],
        channels=[AttributionChannel(**c) for c in result["channels"]],
    )
