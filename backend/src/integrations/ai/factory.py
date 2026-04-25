"""Process-wide adapter selector. One instance per process to keep the
Groq HTTP client alive across requests."""

from __future__ import annotations

from functools import lru_cache

from src.core.config import settings
from src.integrations.ai.base import AIAdapter, AIUnavailableError, DisabledAdapter


@lru_cache(maxsize=1)
def get_ai_adapter() -> AIAdapter:
    provider = settings.ai.provider
    if provider == "groq":
        try:
            from src.integrations.ai.groq_adapter import GroqAdapter

            return GroqAdapter()
        except AIUnavailableError:
            # Fall back silently — log once at boot, keep the app alive.
            import structlog

            structlog.get_logger(__name__).warning(
                "ai_provider_disabled_at_startup",
                reason="groq_init_failed",
            )
            return DisabledAdapter()
    return DisabledAdapter()
