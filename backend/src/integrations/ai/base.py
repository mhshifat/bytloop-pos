"""AI adapter interface.

Same Strategy/Adapter shape as ``integrations.email`` and ``integrations.payments``:
one abstract base class, provider-specific implementations, a factory that
picks the concrete adapter from ``settings.ai.provider``.

The two operations services need are:

* ``complete`` — free-form text in, text out. Used for insight captions,
  chart explanations, anything where we hand the LLM some data and ask
  for prose.
* ``structured`` — same but with a JSON-schema guard. Used for NL-to-SQL
  where we want the model to return a specific shape we can parse without
  regex-wrestling the reply.

Every call carries a hard timeout so an AI outage never blocks a report.
Callers catch ``AIUnavailableError`` and fall back to non-AI output.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class AIUnavailableError(Exception):
    """AI provider is disabled, unreachable, or timed out.

    Services should catch this and degrade gracefully — the app is a POS,
    not a chatbot; analytics without the narrative captions are still useful.
    """


@dataclass(frozen=True, slots=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class AIAdapter(ABC):
    """Provider-agnostic LLM interface."""

    @abstractmethod
    async def complete(
        self,
        *,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Return a plain-text completion."""

    @abstractmethod
    async def structured(
        self,
        *,
        messages: list[Message],
        json_schema: dict[str, Any],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Return a dict matching ``json_schema``.

        Implementations that don't have native JSON-mode should prompt the
        model to return JSON and parse it; parse failures raise
        ``AIUnavailableError``.
        """

    @abstractmethod
    def is_enabled(self) -> bool:
        """True when the provider is configured + reachable. Cheap — no IO."""


class DisabledAdapter(AIAdapter):
    """No-op adapter used when ``AI_PROVIDER=disabled``.

    Every call raises ``AIUnavailableError`` — callers are expected to
    fall back. We return this instance (not None) so the code paths that
    check ``is_enabled()`` stay uniform.
    """

    def is_enabled(self) -> bool:
        return False

    async def complete(
        self,
        *,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        raise AIUnavailableError("AI provider is disabled.")

    async def structured(
        self,
        *,
        messages: list[Message],
        json_schema: dict[str, Any],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        raise AIUnavailableError("AI provider is disabled.")
