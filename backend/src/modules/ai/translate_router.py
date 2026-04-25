"""Cached translation endpoint (no PII).

This is intentionally simple: it takes plain text and returns a translation.
Callers should only send menu/receipt boilerplate (no customer names, addresses, etc.).
"""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Depends
from pydantic import Field

from src.core import cache
from src.core.deps import get_current_user, requires
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.core.errors import ValidationError
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter

router = APIRouter(prefix="/ai", tags=["ai-translate"])


class TranslateRequest(CamelModel):
    source_text: str = Field(min_length=1, max_length=2000)
    target_locale: str = Field(min_length=2, max_length=16)


class TranslateResponse(CamelModel):
    translated_text: str
    cached: bool = False


@router.post(
    "/translate",
    response_model=TranslateResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def translate(
    req: TranslateRequest,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TranslateResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    text = req.source_text.strip()
    if not text:
        raise ValidationError("sourceText is required.")

    locale = req.target_locale.strip().lower()
    if locale in {"en", "en-us", "en-gb"}:
        return TranslateResponse(translated_text=text, cached=True)

    payload = {"t": text, "l": locale}
    digest = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    key = f"pos:ai:tr:{user.tenant_id}:{digest}"
    cached = await cache.get_str(key)
    if cached:
        return TranslateResponse(translated_text=cached, cached=True)

    schema = {
        "type": "object",
        "properties": {"translatedText": {"type": "string"}},
        "required": ["translatedText"],
    }

    sys = (
        "You translate short UI/receipt text.\n"
        "Rules:\n"
        "- Do not add extra commentary.\n"
        "- Keep meaning and tone.\n"
        "- Keep numbers/currency unchanged.\n"
        "- Output JSON only.\n"
        f"Target locale: {locale}\n"
        f"Text: {text}"
    )

    result = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=300,
    )
    out = str(result.get("translatedText", "")).strip()
    if not out:
        raise ValidationError("AI returned an empty translation.")

    await cache.set_str(key, out, ttl_seconds=60 * 60 * 24 * 90)
    return TranslateResponse(translated_text=out, cached=False)

