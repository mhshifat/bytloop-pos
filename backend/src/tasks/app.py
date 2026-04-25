"""Celery application factory.

Uses Redis for broker + result backend, sized to the free-tier budget
(docs/PLAN.md §15b). All pool caps and TTLs match the Global Config.
"""

from __future__ import annotations

from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "bytloop-pos",
    broker=settings.redis.url,
    backend=settings.redis.url,
    include=[
        "src.tasks.email_tasks",
        "src.tasks.cannabis_outbound_tasks",
        "src.tasks.ai_analytics_tasks",
        "src.tasks.personalization_tasks",
    ],
)

celery_app.conf.update(
    # Keep result payloads tiny and short-lived — 20MB Redis ceiling
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "max_connections": settings.redis.max_celery_broker_connections,
        "visibility_timeout": 600,
    },
    redis_backend_settings={
        "max_connections": settings.redis.max_celery_result_connections,
    },
    # Retry policy — exponential backoff with jitter
    task_default_retry_delay=10,
    task_max_retries=5,
    timezone="UTC",
    enable_utc=True,
)

# Beat schedule — cron-style recurring tasks.
celery_app.conf.beat_schedule = {
    "housekeep-every-hour": {
        "task": "src.tasks.email_tasks.noop_healthcheck",
        "schedule": 3600.0,
    },
    "cannabis-compliance-outbox-every-5m": {
        "task": "src.tasks.cannabis_outbound_tasks.compliance_outbox_sync",
        "schedule": 300.0,
    },
    "ai-anomaly-scan-every-30m": {
        "task": "src.tasks.ai_analytics_tasks.scan_anomalies",
        "schedule": 1800.0,
    },
    "ai-forecast-accuracy-every-6h": {
        "task": "src.tasks.ai_analytics_tasks.forecast_accuracy",
        "schedule": 21600.0,
    },
    "p13n-churn-email-cadence-every-6h": {
        "task": "src.tasks.personalization_tasks.churn_email_cadence",
        "schedule": 21600.0,
    },
}
