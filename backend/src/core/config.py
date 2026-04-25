"""Global configuration — single source of truth.

Every tunable behavior in the system is defined here and loaded from environment
variables. No magic numbers, hardcoded provider lists, or duplicated constants
elsewhere. Import ``settings`` and read from it.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class _Base(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def _env_settings(env_prefix: str) -> SettingsConfigDict:
    """Build SettingsConfigDict with a single env_prefix (BaseSettings also sets env_prefix)."""
    return SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=env_prefix,
    )


class AppConfig(_Base):
    model_config = _env_settings("APP_")

    env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = True
    secret_key: SecretStr


class DatabaseConfig(_Base):
    model_config = _env_settings("DATABASE_")

    url: str
    pool_size: int = 8
    max_overflow: int = 4
    pool_recycle_seconds: int = 300
    pool_timeout_seconds: int = 5
    pool_pre_ping: bool = True


class RedisConfig(_Base):
    model_config = _env_settings("REDIS_")

    url: str = "redis://localhost:6379"
    db: int = 0
    max_app_connections: int = 15
    max_celery_broker_connections: int = 8
    max_celery_result_connections: int = 4
    socket_timeout_seconds: float = 2.0
    socket_connect_timeout_seconds: float = 1.0
    op_timeout_seconds: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_cooldown_seconds: int = 30


class AuthConfig(_Base):
    model_config = _env_settings("AUTH_")

    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"

    access_token_ttl_seconds: int = 86400          # 1 day
    refresh_token_ttl_seconds: int = 2_592_000     # 30 days
    activation_token_ttl_seconds: int = 86400      # 1 day
    password_reset_token_ttl_seconds: int = 3600   # 1 hour
    resend_cooldown_seconds: int = 300             # 5 minutes

    password_min_length: int = 8
    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536

    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    github_client_id: str = ""
    github_client_secret: SecretStr = SecretStr("")
    oauth_redirect_base_url: str = "http://localhost:3000"


class CurrencyConfig(_Base):
    model_config = _env_settings("CURRENCY_")

    supported_raw: str = Field(default="BDT,USD", alias="SUPPORTED")
    default: str = "BDT"
    exchange_rate_provider: str = "exchangerate_host"

    @property
    def supported(self) -> list[str]:
        return _csv(self.supported_raw)


class CannabisConfig(_Base):
    """Jurisdiction-configurable compliance knobs for the cannabis vertical.

    Defaults to common US-state limits (28 g / day adult-use). Tenants in
    different jurisdictions override via env.
    """

    model_config = _env_settings("CANNABIS_")

    daily_gram_limit: int = 28
    # Outbound sync targets (placeholders; real connectors are separate work).
    metrc_api_base: str = ""
    biotrack_api_base: str = ""
    biotrack_tenant_id: str = ""
    # Celery worker `src.tasks.cannabis_outbound_tasks` — `off` = no work;
    # `log` = emit structlog, leave rows PENDING; `noop_success` = mark SYNCED
    # (for dev/QA without a state traceability vendor).
    compliance_outbound_mode: Literal["off", "log", "noop_success"] = "off"
    compliance_outbound_batch_size: int = 50
    # For future `log`+HTTP stub: pretend METRC vs BioTrack in logs and payloads.
    compliance_outbound_target: Literal["metrc", "biotrack"] = "metrc"
    # How long the per-customer daily-purchase tally is kept around before
    # the scheduled sweeper can drop it. 90d matches common auditor retention.
    purchase_history_retention_days: int = 90


class AIConfig(_Base):
    """AI / LLM provider configuration.

    Currently uses Groq for fast Llama-3 inference on the hot path (NL→SQL
    reporting + dashboard insight captions). Keep the interface provider-
    agnostic via ``src.integrations.ai.factory`` so OpenAI / Anthropic /
    local ollama can slot in without touching services.
    """

    model_config = _env_settings("AI_")

    provider: Literal["groq", "disabled"] = "disabled"
    # Secret because accidental logging leaks the key; only ``integrations.ai``
    # should ever dereference it.
    groq_api_key: SecretStr | None = None
    # Llama-3.1-8b is cheap + fast enough for captions + NL-SQL; bump to 70b
    # if quality proves insufficient on a tenant's data.
    groq_model: str = "llama-3.1-8b-instant"
    # Hard timeout — AI calls sit on the request path in the NL-QA endpoint
    # and must never hang a tenant's report.
    request_timeout_seconds: int = 15
    # Low temperature for deterministic SQL generation + reproducible captions.
    temperature: float = 0.1
    max_tokens: int = 800


class PaymentConfig(_Base):
    model_config = _env_settings("PAYMENTS_")

    bd_providers_raw: str = Field(
        default="bkash,nagad,sslcommerz,rocket", alias="BD_PROVIDERS"
    )
    global_providers_raw: str = Field(
        default="stripe,paypal", alias="GLOBAL_PROVIDERS"
    )

    @property
    def bd_providers(self) -> list[str]:
        return _csv(self.bd_providers_raw)

    @property
    def global_providers(self) -> list[str]:
        return _csv(self.global_providers_raw)


class EmailConfig(_Base):
    model_config = _env_settings("EMAIL_")

    provider: Literal["smtp", "mailgun", "sendgrid"] = "smtp"
    from_address: str = "no-reply@bytloop-pos.local"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_use_tls: bool = False

    mailgun_api_key: SecretStr = SecretStr("")
    mailgun_domain: str = ""


class CorsConfig(_Base):
    model_config = _env_settings("CORS_")

    allowed_origins_raw: str = Field(
        default="http://localhost:3000", alias="ALLOWED_ORIGINS"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return _csv(self.allowed_origins_raw)


class ObservabilityConfig(_Base):
    model_config = SettingsConfigDict(**_Base.model_config)

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_renderer: Literal["pretty", "json"] = Field(default="pretty", alias="LOG_RENDERER")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    posthog_key: str = Field(default="", alias="POSTHOG_KEY")


class Settings:
    """Aggregated settings — the one object imported across the app."""

    def __init__(self) -> None:
        self.app = AppConfig()  # type: ignore[call-arg]
        self.database = DatabaseConfig()  # type: ignore[call-arg]
        self.redis = RedisConfig()
        self.auth = AuthConfig()  # type: ignore[call-arg]
        self.currency = CurrencyConfig()
        self.payments = PaymentConfig()
        self.email = EmailConfig()
        self.cors = CorsConfig()
        self.observability = ObservabilityConfig()
        self.cannabis = CannabisConfig()
        self.ai = AIConfig()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor — one Settings instance per process."""
    return Settings()


settings = get_settings()
