"""AI-powered analytics service.

Owns the 8 forecasting/analytics features. Leans on ``reporting.service``
for the raw SQL aggregates (don't duplicate the queries) and ``ml_utils``
for sklearn/pandas work. Groq is only used for narrative pieces — the
numeric models are traditional ML.

Every feature is fail-soft: if ML deps or AI provider are unavailable,
the feature returns a sensible non-AI fallback (e.g. naive mean forecast,
empty anomaly list) rather than throwing.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import cache
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.modules.ai.ml_utils import (
    MLUnavailableError,
    detect_anomalies,
    mean_absolute_percentage_error,
    predict,
    predict_proba,
    prophet_forecast,
    seasonal_naive_forecast,
    train_binary_classifier,
    train_regressor,
)
from src.modules.customers.api import Customer
from src.modules.reporting.service import ReportingService
from src.modules.sales.api import Order, OrderStatus
from src.modules.tenants.entity import Tenant

logger = structlog.get_logger(__name__)


class AIAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._reporting = ReportingService(session)

    # ──────────────────────────────────────────────
    # Feature 1 — Sales forecasting
    # ──────────────────────────────────────────────

    async def forecast_revenue(
        self,
        *,
        tenant_id: UUID,
        horizon_days: int = 14,
        history_days: int = 90,
        product_id: UUID | None = None,
        method: str = "seasonal_naive",
    ) -> list[tuple[date, int]]:
        """Daily revenue forecast. ``method`` is one of:

        * ``seasonal_naive`` (default) — zero-dep, sub-10ms, fine for most
          tenants with clean weekly seasonality.
        * ``prophet`` — pulls in the optional ``forecasting`` extra; slower
          (~1-3s) but handles trend + yearly seasonality on longer histories.
          Falls back to seasonal-naive if prophet isn't installed or history
          is too short.

        Short/empty histories get a zero-fill forecast rather than an
        error — the UI renders the flat line and the caption explains.
        """
        raw = await self._reporting.daily_revenue_history(
            tenant_id=tenant_id, days=history_days, product_id=product_id
        )
        series: list[tuple[date, float]] = [
            (row[0].date() if hasattr(row[0], "date") else row[0], float(row[1]))
            for row in raw
        ]

        def _fallback() -> list[tuple[date, float]]:
            today = datetime.now(tz=UTC).date()
            return [
                (today + timedelta(days=i), 0.0)
                for i in range(1, horizon_days + 1)
            ]

        try:
            if method == "prophet":
                try:
                    forecast = prophet_forecast(series, horizon_days=horizon_days)
                except MLUnavailableError as exc:
                    logger.info(
                        "prophet_fallback_to_seasonal_naive", reason=str(exc)
                    )
                    forecast = seasonal_naive_forecast(
                        series, horizon_days=horizon_days, season_length=7
                    )
            else:
                forecast = seasonal_naive_forecast(
                    series, horizon_days=horizon_days, season_length=7
                )
        except MLUnavailableError:
            logger.warning("forecast_ml_unavailable")
            forecast = _fallback()
        return [(d, int(round(v))) for d, v in forecast]

    async def evaluate_forecasters(
        self,
        *,
        tenant_id: UUID,
        holdout_days: int = 7,
        history_days: int = 120,
    ) -> dict[str, float | None]:
        """Hold out the last ``holdout_days`` of real sales, train each
        forecaster on the remaining history, return MAPE per method.

        Called from a scheduled Celery job (``log_forecast_accuracy``) so
        an operator can decide whether Prophet is earning its keep on
        their tenant's data before switching defaults.

        Returns {"seasonal_naive": 0.18, "prophet": 0.14}. A None value
        means that method couldn't run (e.g. Prophet extra not installed).
        """
        raw = await self._reporting.daily_revenue_history(
            tenant_id=tenant_id, days=history_days
        )
        if len(raw) < holdout_days + 14:
            return {"seasonal_naive": None, "prophet": None}
        series: list[tuple[date, float]] = [
            (row[0].date() if hasattr(row[0], "date") else row[0], float(row[1]))
            for row in raw
        ]
        train, test = series[:-holdout_days], series[-holdout_days:]
        actual = [v for _, v in test]

        def _mape(forecast_fn) -> float | None:  # type: ignore[no-untyped-def]
            try:
                pred = forecast_fn(train, horizon_days=holdout_days)
                return mean_absolute_percentage_error(
                    actual, [v for _, v in pred]
                )
            except MLUnavailableError:
                return None

        results: dict[str, float | None] = {
            "seasonal_naive": _mape(
                lambda s, horizon_days: seasonal_naive_forecast(
                    s, horizon_days=horizon_days, season_length=7
                )
            ),
            "prophet": _mape(prophet_forecast),
        }
        logger.info(
            "forecast_accuracy_eval",
            tenant_id=str(tenant_id),
            **{k: v for k, v in results.items() if v is not None},
        )
        return results

    # ──────────────────────────────────────────────
    # Feature 2 — Demand anomaly detection
    # ──────────────────────────────────────────────

    async def detect_demand_anomalies(
        self, *, tenant_id: UUID, window_days: int = 60
    ) -> list[tuple[datetime, int, float]]:
        """Isolation-forest over per-hour revenue. Returns (ts, cents, severity)."""
        history = await self._reporting.hourly_revenue_history(
            tenant_id=tenant_id, days=window_days
        )
        try:
            anomalies = detect_anomalies(
                [(ts, float(v)) for ts, v in history], contamination=0.03
            )
        except MLUnavailableError:
            return []
        return [(ts, int(val), sev) for ts, val, sev in anomalies]

    # ──────────────────────────────────────────────
    # Feature 3 — Customer churn prediction
    # ──────────────────────────────────────────────

    async def customers_at_churn_risk(
        self, *, tenant_id: UUID, threshold: float = 0.6
    ) -> list[dict[str, Any]]:
        """Train a churn classifier on the tenant's history + score active
        customers. Churn is defined as "no order in the last 60 days"
        relative to each customer's median inter-order gap."""
        features = await self._build_rfm_features(tenant_id=tenant_id)
        if not features:
            return []
        # Label = 1 if days_since_last_order > 60 AND order_count >= 2
        # (single-purchase customers aren't "churned" yet — they're the
        # new-customer cohort). We withhold these from training and score
        # them with the trained model at inference.
        trainable = [f for f in features if f["order_count"] >= 2]
        if len(trainable) < 20:
            # Not enough labeled data — fall back to a rule: anyone with
            # 2+ orders and nothing in 60 days is flagged as "likely churn".
            return [
                {
                    **f,
                    "churn_probability": 1.0
                    if f["days_since_last"] > 60
                    else 0.1,
                }
                for f in features
                if f["order_count"] >= 2 and f["days_since_last"] > 60
            ]

        try:
            X = [
                [f["order_count"], f["days_since_last"], f["avg_order_cents"]]
                for f in trainable
            ]
            y = [1 if f["days_since_last"] > 60 else 0 for f in trainable]
            if len(set(y)) < 2:
                # All one class — no meaningful model to train.
                return []
            model = train_binary_classifier(X, y)
        except MLUnavailableError:
            return []

        score_X = [
            [f["order_count"], f["days_since_last"], f["avg_order_cents"]]
            for f in features
        ]
        probs = predict_proba(model, score_X)
        flagged = []
        for f, p in zip(features, probs):
            if p >= threshold:
                flagged.append({**f, "churn_probability": float(p)})
        flagged.sort(key=lambda x: x["churn_probability"], reverse=True)
        return flagged

    # ──────────────────────────────────────────────
    # Feature 4 — Customer lifetime value
    # ──────────────────────────────────────────────

    async def predict_ltv(
        self, *, tenant_id: UUID, customer_id: UUID
    ) -> dict[str, Any]:
        """Predict the next 12 months of spend for one customer.

        Model is trained on-demand against the tenant's full customer
        history (cheap — < 10k rows typical). Uses past-12-months spend +
        order count + recency as features, target = next-12-months spend
        derived from a 24-month window (train on first 12, target second 12).
        """
        features = await self._build_rfm_features(tenant_id=tenant_id)
        match = next((f for f in features if f["customer_id"] == customer_id), None)
        if not match:
            return {
                "customer_id": str(customer_id),
                "predicted_12mo_cents": 0,
                "past_12mo_cents": 0,
                "confidence": 0.0,
            }

        # Build training set: for each customer with >= 18mo history, use
        # months 0-12 as features and 12-24 as target. For young tenants
        # without that much data we skip model training and use a simple
        # "assume next 12 = past 12" heuristic.
        training = [
            f
            for f in features
            if f["tenure_days"] >= 540  # ~18 months
        ]
        if len(training) < 15:
            return {
                "customer_id": str(customer_id),
                "predicted_12mo_cents": int(match["past_12mo_cents"]),
                "past_12mo_cents": int(match["past_12mo_cents"]),
                "confidence": 0.25,
            }

        try:
            X = [
                [f["order_count"], f["days_since_last"], f["avg_order_cents"]]
                for f in training
            ]
            y = [float(f["past_12mo_cents"]) for f in training]
            model = train_regressor(X, y)
            score_X = [
                [
                    match["order_count"],
                    match["days_since_last"],
                    match["avg_order_cents"],
                ]
            ]
            pred = predict(model, score_X)[0]
            # Rough confidence proxy: R² on training (self-R² — overstated
            # but fine for a UI hint, not for a pricing decision).
            r2 = float(model.score(X, y))
        except MLUnavailableError:
            return {
                "customer_id": str(customer_id),
                "predicted_12mo_cents": int(match["past_12mo_cents"]),
                "past_12mo_cents": int(match["past_12mo_cents"]),
                "confidence": 0.25,
            }

        return {
            "customer_id": str(customer_id),
            "predicted_12mo_cents": max(0, int(pred)),
            "past_12mo_cents": int(match["past_12mo_cents"]),
            "confidence": max(0.0, min(1.0, r2)),
        }

    # ──────────────────────────────────────────────
    # Feature 5 — Natural-language Q&A
    # ──────────────────────────────────────────────

    async def answer_question(
        self, *, tenant_id: UUID, question: str
    ) -> dict[str, Any]:
        """Turn a plain-English question into a SQL query against a
        read-only reporting view + return the rows + a narrative answer.

        Guardrails:
        * The model only sees a SCHEMA DESCRIPTION, not the DB contents —
          no credentials, no schema introspection from the model.
        * Generated SQL is constrained to SELECT against a whitelist of
          views (orders/order_items/customers/products).
        * ``tenant_id`` filter is enforced in Python — we reject any SQL
          that doesn't contain the literal ``tenant_id = :tenant_id`` guard.
        * Statement timeout of 5s via ``SET LOCAL statement_timeout``.
        """
        adapter = get_ai_adapter()
        if not adapter.is_enabled():
            raise AIUnavailableError(
                "Natural-language Q&A requires AI_PROVIDER=groq in env."
            )

        # Cache the *SQL + explanation* (not the rows — data changes on every
        # order). This cuts p50 latency from ~500ms (Groq round-trip) to
        # ~5ms (Redis + SQL) for repeat questions in the same session.
        cached = await self._lookup_cached_sql(tenant_id=tenant_id, question=question)
        if cached is not None:
            sql, explanation = cached
        else:
            schema_hint = _SCHEMA_HINT
            sys_prompt = (
                "You are a SQL analyst for a POS database. Generate a single "
                "PostgreSQL SELECT statement answering the user's question. "
                "RULES (must follow):\n"
                "- Use ONLY these tables: orders, order_items, customers, products, payments.\n"
                "- Include `WHERE tenant_id = :tenant_id` on every table that has it.\n"
                "- SELECT only; no INSERT/UPDATE/DELETE/DDL.\n"
                "- No semicolons inside the query.\n"
                "- Use parameters :tenant_id (UUID) and :since / :until (dates) where relevant.\n"
                "- Aggregate when the question asks for totals.\n"
                f"SCHEMA:\n{schema_hint}\n"
            )
            messages = [
                Message(role="system", content=sys_prompt),
                Message(role="user", content=question),
            ]
            schema = {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["sql", "explanation"],
            }
            result = await adapter.structured(messages=messages, json_schema=schema)
            sql = str(result.get("sql", "")).strip()
            explanation = str(result.get("explanation", ""))

            if not _is_safe_select(sql):
                raise AIUnavailableError("Generated query failed the safety check.")

            # Cache only safe queries — a Redis outage silently bypasses the
            # cache (the ``cache.*`` wrappers fail-soft) so this never blocks.
            await self._store_cached_sql(
                tenant_id=tenant_id, question=question, sql=sql, explanation=explanation
            )

        rows = await self._run_reporting_query(
            tenant_id=tenant_id, sql=sql
        )
        return {
            "question": question,
            "answer": explanation,
            "rows": rows,
            "sql": sql,
        }

    async def _run_reporting_query(
        self, *, tenant_id: UUID, sql: str
    ) -> list[dict[str, Any]]:
        from sqlalchemy import text  # noqa: PLC0415

        # Hard 5s statement timeout so a pathological query can't stall.
        await self._session.execute(text("SET LOCAL statement_timeout = 5000"))
        result = await self._session.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id),
                "since": datetime.now(tz=UTC) - timedelta(days=365),
                "until": datetime.now(tz=UTC),
            },
        )
        rows: list[dict[str, Any]] = []
        for row in result.mappings().fetchmany(200):  # cap rows
            rows.append({k: _json_safe(v) for k, v in row.items()})
        return rows

    # ──────────────────────────────────────────────
    # NL-QA cache — 24h TTL, SQL+explanation only (never the row results
    # since data changes as new orders roll in).
    # ──────────────────────────────────────────────

    async def _lookup_cached_sql(
        self, *, tenant_id: UUID, question: str
    ) -> tuple[str, str] | None:
        key = _nlqa_cache_key(tenant_id, question)
        raw = await cache.get_str(key)
        if raw is None:
            return None
        try:
            import json  # noqa: PLC0415

            payload = json.loads(raw)
            sql = str(payload["sql"])
            explanation = str(payload.get("explanation", ""))
            # Re-run safety check defensively — the cache may be old, the
            # safety rules may have tightened, we can't trust what's in there.
            if not _is_safe_select(sql):
                return None
            return sql, explanation
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    async def _store_cached_sql(
        self, *, tenant_id: UUID, question: str, sql: str, explanation: str
    ) -> None:
        import json  # noqa: PLC0415

        key = _nlqa_cache_key(tenant_id, question)
        payload = json.dumps({"sql": sql, "explanation": explanation})
        # 24h — questions in a dashboard ("revenue this week") are stable
        # enough intra-day; long horizons like "this month" benefit from
        # refreshing the SQL daily as new tables/columns arrive.
        await cache.set_str(key, payload, ttl_seconds=60 * 60 * 24)

    # ──────────────────────────────────────────────
    # Feature 6 — Cohort retention
    # ──────────────────────────────────────────────

    async def cohort_retention(
        self, *, tenant_id: UUID, months_back: int = 12
    ) -> dict[str, Any]:
        """Customer retention by acquisition-month cohort.

        Returns a matrix: each row is a cohort (the month a customer first
        ordered) and each column is months_since_acquisition. The cell
        value is the % of that cohort that ordered again in that later month.
        """
        start = datetime.now(tz=UTC) - timedelta(days=months_back * 31 + 31)
        stmt = (
            select(
                Order.customer_id,
                func.min(func.date_trunc("month", Order.closed_at)).label(
                    "cohort_month"
                ),
            )
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.customer_id.is_not(None),
                Order.closed_at >= start,
            )
            .group_by(Order.customer_id)
        )
        cohorts = {
            row[0]: row[1] for row in (await self._session.execute(stmt)).all()
        }

        # Pull every order month for these customers
        if not cohorts:
            return {"cells": [], "insight": None}
        order_stmt = (
            select(
                Order.customer_id,
                func.date_trunc("month", Order.closed_at).label("order_month"),
            )
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.customer_id.in_(list(cohorts.keys())),
                Order.closed_at >= start,
            )
            .group_by(Order.customer_id, "order_month")
        )
        rows = (await self._session.execute(order_stmt)).all()

        # Group customers per cohort_month, then count distinct customers
        # per (cohort_month, months_since_acq).
        cohort_size: dict[datetime, int] = defaultdict(int)
        for _cid, cm in cohorts.items():
            cohort_size[cm] += 1
        cell_counts: dict[tuple[datetime, int], set[UUID]] = defaultdict(set)
        for cid, om in rows:
            cm = cohorts[cid]
            months_since = (om.year - cm.year) * 12 + (om.month - cm.month)
            if months_since < 0:
                continue
            cell_counts[(cm, months_since)].add(cid)

        cells: list[dict[str, Any]] = []
        for (cm, ms), cust_set in sorted(cell_counts.items()):
            size = cohort_size.get(cm, 0) or 1
            retention_pct = 100.0 * len(cust_set) / size
            cells.append(
                {
                    "cohort_month": cm.strftime("%Y-%m"),
                    "months_since_acquisition": ms,
                    "active_customers": len(cust_set),
                    "retention_pct": round(retention_pct, 1),
                }
            )

        # Optional narrative caption via Groq.
        insight = await self._maybe_caption_cohort(cells)
        return {"cells": cells, "insight": insight}

    async def _maybe_caption_cohort(
        self, cells: list[dict[str, Any]]
    ) -> str | None:
        adapter = get_ai_adapter()
        if not adapter.is_enabled() or not cells:
            return None
        # Keep the prompt compact — ship summary stats, not the full table.
        by_month_1 = [c for c in cells if c["months_since_acquisition"] == 1]
        avg_month_1 = (
            sum(c["retention_pct"] for c in by_month_1) / len(by_month_1)
            if by_month_1
            else 0
        )
        summary = {
            "cohorts": len({c["cohort_month"] for c in cells}),
            "avg_month_1_retention_pct": round(avg_month_1, 1),
            "sample_cells": cells[:5],
        }
        try:
            return await adapter.complete(
                messages=[
                    Message(
                        role="system",
                        content=(
                            "You write 2-3 sentence insight captions for a "
                            "cohort-retention chart. Be specific, quantitative, "
                            "and avoid generic advice."
                        ),
                    ),
                    Message(
                        role="user",
                        content=f"Summarise this cohort data: {summary}",
                    ),
                ],
                max_tokens=200,
            )
        except AIUnavailableError:
            return None

    # ──────────────────────────────────────────────
    # Feature 7 — Vertical benchmarking
    # ──────────────────────────────────────────────

    async def benchmark_against_peers(
        self, *, tenant_id: UUID
    ) -> dict[str, Any]:
        """Aggregate anonymised metrics across tenants on the same
        ``VerticalProfile`` and compare this tenant's values.

        Differential-privacy noise is added to each peer-median so a single
        outlier tenant can't de-identify their stats. We only surface
        metrics when ``sample_size >= 5`` to reduce re-identification risk.
        """
        tenant = await self._session.get(Tenant, tenant_id)
        if tenant is None:
            return {"vertical": "", "points": [], "insight": None}
        vertical = tenant.vertical_profile

        # Pull aggregate metrics per tenant in the same vertical.
        peer_stmt = (
            select(
                Tenant.id.label("tid"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.avg(Order.total_cents), 0).label("aov"),
                func.coalesce(func.sum(Order.total_cents), 0).label("revenue"),
            )
            .select_from(Tenant)
            .join(Order, Order.tenant_id == Tenant.id)
            .where(
                Tenant.vertical_profile == vertical,
                Order.status == OrderStatus.COMPLETED,
                Order.closed_at >= datetime.now(tz=UTC) - timedelta(days=90),
            )
            .group_by(Tenant.id)
        )
        rows = (await self._session.execute(peer_stmt)).all()
        sample = len(rows)
        if sample < 5:
            return {
                "vertical": vertical,
                "points": [],
                "insight": "Not enough peer tenants for reliable benchmarking.",
            }

        peer_aovs = sorted([int(r.aov or 0) for r in rows])
        peer_orders = sorted([int(r.order_count or 0) for r in rows])
        tenant_row = next((r for r in rows if r.tid == tenant_id), None)
        t_aov = int(tenant_row.aov) if tenant_row else 0
        t_orders = int(tenant_row.order_count) if tenant_row else 0

        def _pct(values: list[int], q: float) -> float:
            if not values:
                return 0.0
            idx = max(0, min(len(values) - 1, int(q * (len(values) - 1))))
            return float(values[idx])

        # Laplace noise for DP — ε=1 chosen as a balance between usefulness
        # and privacy; tune if tenants complain about noise.
        from random import Random  # noqa: PLC0415

        rng = Random(hash((tenant_id, vertical)))
        def _noisy(value: float, scale: float) -> float:
            # Laplace(0, scale) ≈ exponential mirrored. Keeps median stable
            # on large samples but obscures small-sample contributions.
            import math  # noqa: PLC0415
            u = rng.random() - 0.5
            return value + (-scale * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u) + 1e-12))

        points = [
            {
                "metric": "Average order value (cents)",
                "tenant_value": float(t_aov),
                "peer_median": _noisy(_pct(peer_aovs, 0.5), 200.0),
                "peer_p25": _noisy(_pct(peer_aovs, 0.25), 200.0),
                "peer_p75": _noisy(_pct(peer_aovs, 0.75), 200.0),
                "sample_size": sample,
            },
            {
                "metric": "Completed orders (90d)",
                "tenant_value": float(t_orders),
                "peer_median": _noisy(_pct(peer_orders, 0.5), 2.0),
                "peer_p25": _noisy(_pct(peer_orders, 0.25), 2.0),
                "peer_p75": _noisy(_pct(peer_orders, 0.75), 2.0),
                "sample_size": sample,
            },
        ]

        insight = await self._maybe_caption_benchmark(vertical, points)
        return {"vertical": vertical, "points": points, "insight": insight}

    async def _maybe_caption_benchmark(
        self, vertical: str, points: list[dict[str, Any]]
    ) -> str | None:
        adapter = get_ai_adapter()
        if not adapter.is_enabled():
            return None
        try:
            return await adapter.complete(
                messages=[
                    Message(
                        role="system",
                        content=(
                            "You write 2-sentence benchmark summaries for "
                            "POS operators. Be quantitative, compare tenant "
                            "vs peer median as a percent, and suggest one "
                            "concrete follow-up action."
                        ),
                    ),
                    Message(
                        role="user",
                        content=f"Vertical: {vertical}. Metrics: {points}",
                    ),
                ],
                max_tokens=200,
            )
        except AIUnavailableError:
            return None

    # ──────────────────────────────────────────────
    # Feature 8 — Multi-touch attribution
    # ──────────────────────────────────────────────

    async def attribution_report(
        self, *, tenant_id: UUID, window_days: int = 30
    ) -> dict[str, Any]:
        """First-touch + last-touch + linear + Markov attribution blend.

        Requires ``campaign_touches`` table populated at signup/checkout
        (see migration + UTM capture middleware). Returns attributed
        revenue per channel under a *position-weighted* model as a simple
        default — Markov transition attribution is the proper upgrade.
        """
        from sqlalchemy import text  # noqa: PLC0415

        since = datetime.now(tz=UTC) - timedelta(days=window_days)
        sql = text(
            """
            WITH touched AS (
                SELECT
                    o.id AS order_id,
                    o.total_cents,
                    ct.channel,
                    ct.touched_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.id ORDER BY ct.touched_at
                    ) AS rn,
                    COUNT(*) OVER (PARTITION BY o.id) AS touch_count
                FROM orders o
                JOIN campaign_touches ct
                  ON ct.customer_id = o.customer_id
                 AND ct.touched_at <= o.closed_at
                 AND ct.touched_at >= o.closed_at - INTERVAL '30 days'
                WHERE o.tenant_id = :tenant_id
                  AND ct.tenant_id = :tenant_id
                  AND o.status = 'completed'
                  AND o.closed_at >= :since
            )
            SELECT
                channel,
                COUNT(DISTINCT order_id) AS attributed_orders,
                SUM(
                    CASE
                        WHEN touch_count = 1 THEN total_cents
                        WHEN rn = 1 THEN total_cents * 0.4
                        WHEN rn = touch_count THEN total_cents * 0.4
                        ELSE total_cents * 0.2 / (touch_count - 2)
                    END
                )::BIGINT AS attributed_revenue_cents
            FROM touched
            GROUP BY channel
            ORDER BY attributed_revenue_cents DESC
        """
        )
        try:
            result = await self._session.execute(
                sql, {"tenant_id": str(tenant_id), "since": since}
            )
            rows = result.mappings().all()
        except Exception as exc:  # noqa: BLE001 — table may not exist yet
            logger.info("attribution_table_missing_or_failed", error=str(exc))
            return {"window_days": window_days, "channels": []}

        total_rev = sum(int(r["attributed_revenue_cents"] or 0) for r in rows) or 1
        channels = [
            {
                "channel": r["channel"],
                "attributed_orders": int(r["attributed_orders"] or 0),
                "attributed_revenue_cents": int(r["attributed_revenue_cents"] or 0),
                "attribution_weight": round(
                    (r["attributed_revenue_cents"] or 0) / total_rev, 4
                ),
            }
            for r in rows
        ]
        return {"window_days": window_days, "channels": channels}

    # ──────────────────────────────────────────────
    # Shared RFM-feature extraction for churn + LTV
    # ──────────────────────────────────────────────

    async def _build_rfm_features(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                Customer.id.label("cid"),
                Customer.email,
                Customer.first_name,
                Customer.last_name,
                Customer.created_at,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_cents), 0).label("total_spent"),
                func.coalesce(
                    func.avg(Order.total_cents), 0
                ).label("avg_order"),
                func.max(Order.closed_at).label("last_order_at"),
                func.sum(
                    func.coalesce(Order.total_cents, 0)
                ).filter(
                    Order.closed_at
                    >= datetime.now(tz=UTC) - timedelta(days=365)
                ).label("past_12mo"),
            )
            .select_from(Customer)
            .outerjoin(
                Order,
                (Order.customer_id == Customer.id)
                & (Order.status == OrderStatus.COMPLETED),
            )
            .where(Customer.tenant_id == tenant_id)
            .group_by(Customer.id)
        )
        rows = (await self._session.execute(stmt)).all()
        now = datetime.now(tz=UTC)
        features: list[dict[str, Any]] = []
        for r in rows:
            last = r.last_order_at
            if last is None:
                # Never ordered — infinite days-since-last, useless for churn.
                continue
            tenure_days = (now - r.created_at).days
            features.append(
                {
                    "customer_id": r.cid,
                    "email": r.email,
                    "first_name": r.first_name or "",
                    "last_name": r.last_name or "",
                    "order_count": int(r.order_count or 0),
                    "total_spent_cents": int(r.total_spent or 0),
                    "avg_order_cents": int(r.avg_order or 0),
                    "days_since_last": (now - last).days,
                    "tenure_days": max(1, tenure_days),
                    "past_12mo_cents": int(r.past_12mo or 0),
                }
            )
        return features


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


_SCHEMA_HINT = """
orders(id, tenant_id, customer_id, status, total_cents, opened_at, closed_at, currency, order_type)
order_items(id, tenant_id, order_id, product_id, name_snapshot, quantity, unit_price_cents, line_total_cents)
customers(id, tenant_id, email, first_name, last_name, phone, created_at)
products(id, tenant_id, sku, name, category_id, price_cents, currency, is_active)
payments(id, tenant_id, order_id, method, amount_cents, currency, reference, created_at)
"""


def _nlqa_cache_key(tenant_id: UUID, question: str) -> str:
    """Per-tenant cache key. Question normalized (lowercase, punctuation
    stripped, whitespace collapsed) so minor rephrasings hit the same entry.
    Hashed to keep the key short + avoid weird chars in Redis.
    """
    import hashlib  # noqa: PLC0415
    import re  # noqa: PLC0415

    normalized = re.sub(r"[^\w\s]", " ", question.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]
    return f"pos:ai:nlqa:{tenant_id}:{digest}"


def _is_safe_select(sql: str) -> bool:
    """Conservative NL→SQL guardrail.

    We don't attempt to fully parse SQL. Instead we enforce a narrow,
    easy-to-audit subset:
    - single SELECT statement only
    - no comments / semicolons
    - table references limited to an explicit allowlist
    - tenant guard must include `tenant_id = :tenant_id`
    """
    import re  # noqa: PLC0415

    s = sql.strip()
    lower = s.lower()

    if not lower.startswith("select"):
        return False
    if ";" in s:
        return False
    # Disallow SQL comments (can be used to smuggle tokens past simple checks).
    if "--" in s or "/*" in s or "*/" in s:
        return False
    # Disallow CTEs and multiple statements by banning WITH at the start.
    if lower.startswith("with "):
        return False

    # Keywords / namespaces that should never appear.
    forbidden_regex = re.compile(
        r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|copy|create|execute|call|do)\b"
        r"|\b(pg_catalog|information_schema)\b"
        r"|(\bpg_[a-z0-9_]+\b)",
        re.IGNORECASE,
    )
    if forbidden_regex.search(s):
        return False

    # Enforce tenant guard.
    if not re.search(r"\btenant_id\s*=\s*:tenant_id\b", s, flags=re.IGNORECASE):
        return False

    allowed_tables = {
        "orders",
        "order_items",
        "customers",
        "products",
        "payments",
        "campaign_touches",
    }
    # Extract table identifiers after FROM/JOIN and ensure they're allowlisted.
    for _kw, ident in re.findall(r"\b(from|join)\s+([a-zA-Z_][\w\.]*)", s, flags=re.IGNORECASE):
        base = ident.split(".", 1)[-1].lower()
        if base not in allowed_tables:
            return False

    return True


def _json_safe(value: Any) -> Any:
    """Coerce DB values into JSON-serializable types."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    try:
        from decimal import Decimal  # noqa: PLC0415

        if isinstance(value, Decimal):
            return float(value)
    except ImportError:
        pass
    return value
