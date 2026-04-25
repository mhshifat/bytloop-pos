"""Groq adapter — Llama-3 family via the Groq Cloud API.

Groq is fast (sub-second for short prompts on 8b models) which matters for
the NL-QA hot path where the user is staring at a spinner. The official
SDK is sync; we wrap it in ``asyncio.to_thread`` so it doesn't block the
event loop.

Fail-open posture: any timeout, rate-limit, API-error, or JSON-parse error
is raised as ``AIUnavailableError`` so callers can degrade to non-AI output.
Never let an AI hiccup take down a report.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog

from src.core.config import settings
from src.integrations.ai.base import (
    AIAdapter,
    AIUnavailableError,
    Message,
)

logger = structlog.get_logger(__name__)


class GroqAdapter(AIAdapter):
    def __init__(self) -> None:
        key = settings.ai.groq_api_key
        if key is None:
            raise AIUnavailableError(
                "AI_GROQ_API_KEY is missing — set it in env or switch AI_PROVIDER to 'disabled'."
            )
        # Lazy import so the app still boots when ``groq`` isn't installed
        # (e.g. a minimal dev container without the AI deps).
        try:
            from groq import Groq
        except ImportError as exc:  # noqa: BLE001
            raise AIUnavailableError(
                "groq package is not installed; run `uv sync`."
            ) from exc
        self._client = Groq(
            api_key=key.get_secret_value(),
            timeout=settings.ai.request_timeout_seconds,
        )
        self._model = settings.ai.groq_model

    def is_enabled(self) -> bool:
        return True

    async def complete(
        self,
        *,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.chat.completions.create,
                    model=self._model,
                    messages=payload,
                    max_tokens=max_tokens or settings.ai.max_tokens,
                    temperature=temperature
                    if temperature is not None
                    else settings.ai.temperature,
                ),
                timeout=settings.ai.request_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("groq_timeout")
            raise AIUnavailableError("AI request timed out.") from exc
        except Exception as exc:  # noqa: BLE001 — provider errors are opaque
            logger.warning("groq_api_error", error=str(exc))
            raise AIUnavailableError(f"AI provider error: {exc}") from exc

        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError) as exc:
            raise AIUnavailableError("AI provider returned an unexpected shape.") from exc
        return content or ""

    async def structured(
        self,
        *,
        messages: list[Message],
        json_schema: dict[str, Any],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        # Groq supports JSON mode via response_format={"type": "json_object"}.
        # We inject the schema into the system prompt so the model knows the
        # expected shape — response_format alone doesn't enforce structure.
        schema_hint = json.dumps(json_schema, indent=2)
        guarded = [
            *messages,
            Message(
                role="system",
                content=(
                    "You MUST respond with a single JSON object matching this schema:\n"
                    f"{schema_hint}\n"
                    "No prose, no code fences, no leading text. Just JSON."
                ),
            ),
        ]
        payload = [{"role": m.role, "content": m.content} for m in guarded]
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.chat.completions.create,
                    model=self._model,
                    messages=payload,
                    max_tokens=max_tokens or settings.ai.max_tokens,
                    temperature=temperature
                    if temperature is not None
                    else settings.ai.temperature,
                    response_format={"type": "json_object"},
                ),
                timeout=settings.ai.request_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("groq_timeout")
            raise AIUnavailableError("AI request timed out.") from exc
        except Exception as exc:  # noqa: BLE001
            logger.warning("groq_api_error", error=str(exc))
            raise AIUnavailableError(f"AI provider error: {exc}") from exc

        try:
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except (IndexError, AttributeError, json.JSONDecodeError) as exc:
            logger.warning("groq_json_parse_failed", error=str(exc))
            raise AIUnavailableError("AI provider returned invalid JSON.") from exc
