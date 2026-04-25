from __future__ import annotations

from src.core.schemas import CamelModel


class SalesSummary(CamelModel):
    order_count: int
    revenue_cents: int


class DashboardSnapshot(CamelModel):
    today: SalesSummary
    last7_days: SalesSummary
    customer_count: int = 0
    low_stock_count: int = 0


class DailySalesPoint(CamelModel):
    day: str
    order_count: int
    revenue_cents: int


class TopProductPoint(CamelModel):
    product_id: str
    name: str
    sku: str
    units_sold: int
    revenue_cents: int


class PaymentMethodPoint(CamelModel):
    method: str
    order_count: int
    amount_cents: int


# ──────────────────────────────────────────────────────────────────────────
# AI / forecast shapes
# ──────────────────────────────────────────────────────────────────────────


class ForecastPoint(CamelModel):
    day: str
    forecast_revenue_cents: int
    forecast_units: int | None = None


class ForecastResult(CamelModel):
    horizon_days: int
    generated_at: str
    points: list[ForecastPoint]
    # Non-null only when a specific product_id was requested.
    product_id: str | None = None


class AnomalyPoint(CamelModel):
    timestamp: str
    revenue_cents: int
    severity: float  # 0 = normal, 1 = most anomalous
    note: str | None = None


class AnomalyReport(CamelModel):
    window_days: int
    anomalies: list[AnomalyPoint]


class ChurnRiskCustomer(CamelModel):
    customer_id: str
    email: str | None
    first_name: str
    last_name: str
    days_since_last_order: int
    order_count: int
    total_spent_cents: int
    churn_probability: float  # 0..1


class ChurnReport(CamelModel):
    threshold: float
    customers: list[ChurnRiskCustomer]


class LifetimeValuePrediction(CamelModel):
    customer_id: str
    predicted_12mo_cents: int
    past_12mo_cents: int
    confidence: float  # 0..1 crude — R² of the model on the tenant's data


class CohortCell(CamelModel):
    cohort_month: str
    months_since_acquisition: int
    active_customers: int
    retention_pct: float


class CohortReport(CamelModel):
    cells: list[CohortCell]
    insight: str | None = None


class BenchmarkPoint(CamelModel):
    metric: str
    tenant_value: float
    peer_median: float
    peer_p25: float
    peer_p75: float
    sample_size: int


class BenchmarkReport(CamelModel):
    vertical: str
    points: list[BenchmarkPoint]
    insight: str | None = None


class NLQuestion(CamelModel):
    question: str


class NLAnswer(CamelModel):
    question: str
    answer: str
    rows: list[dict[str, object]] = []
    sql: str | None = None


class AttributionChannel(CamelModel):
    channel: str
    attributed_orders: int
    attributed_revenue_cents: int
    attribution_weight: float


class AttributionReport(CamelModel):
    window_days: int
    channels: list[AttributionChannel]
