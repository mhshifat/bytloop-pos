"""AI helpers for catalog workflows (descriptions, transcript-driven drafts)."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import Field

from src.core import cache
from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import ValidationError
from src.core.permissions import Permission
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.modules.catalog.schemas import ProductUpdate
from src.modules.catalog.service import CatalogService
from src.core.schemas import CamelModel

router = APIRouter(prefix="/ai/catalog", tags=["ai-catalog"])


class ProductDescriptionResult(CamelModel):
    product_id: UUID
    description: str
    cached: bool = False


@router.post(
    "/products/{product_id}/generate-description",
    response_model=ProductDescriptionResult,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def generate_description(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductDescriptionResult:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    product = await CatalogService(db).get_product(
        tenant_id=user.tenant_id, product_id=product_id
    )

    # Cache key includes the fields that affect the generation.
    cache_payload = {
        "sku": product.sku,
        "name": product.name,
        "category_id": str(product.category_id) if product.category_id else None,
        "price_cents": product.price_cents,
        "currency": product.currency,
    }
    digest = hashlib.sha1(json.dumps(cache_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    key = f"pos:ai:prod_desc:{user.tenant_id}:{product_id}:{digest}"
    cached = await cache.get_str(key)
    if cached:
        return ProductDescriptionResult(
            product_id=product_id,
            description=cached,
            cached=True,
        )

    schema = {
        "type": "object",
        "properties": {"description": {"type": "string"}},
        "required": ["description"],
    }
    prompt = (
        "Write a concise, helpful product description for a POS catalog.\n"
        "Rules:\n"
        "- 1-3 short paragraphs.\n"
        "- No unverifiable claims.\n"
        "- No emojis.\n"
        "- Keep it under 600 characters.\n"
        "- Output JSON only.\n"
        f"Product:\n"
        f"- SKU: {product.sku}\n"
        f"- Name: {product.name}\n"
        f"- Price: {product.currency} {product.price_cents/100:.2f}\n"
    )
    result = await adapter.structured(
        messages=[Message(role="system", content=prompt)],
        json_schema=schema,
        temperature=0.3,
        max_tokens=300,
    )
    description = str(result.get("description", "")).strip()
    if not description:
        raise ValidationError("AI returned an empty description.")
    if len(description) > 1200:
        description = description[:1200].rstrip()

    await cache.set_str(key, description, ttl_seconds=60 * 60 * 24 * 30)
    return ProductDescriptionResult(product_id=product_id, description=description, cached=False)


class VoiceProductDraftRequest(CamelModel):
    transcript: str = Field(min_length=1, max_length=4000)


class VoiceProductDraft(CamelModel):
    sku: str | None = None
    barcode: str | None = None
    name: str
    description: str | None = None
    category_name: str | None = None
    price_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


@router.post(
    "/voice-product",
    response_model=VoiceProductDraft,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def voice_product_draft(
    req: VoiceProductDraftRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VoiceProductDraft:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    transcript = req.transcript.strip()
    if len(transcript) < 4:
        raise ValidationError("Transcript is too short.")

    schema = {
        "type": "object",
        "properties": {
            "sku": {"type": ["string", "null"]},
            "barcode": {"type": ["string", "null"]},
            "name": {"type": "string"},
            "description": {"type": ["string", "null"]},
            "categoryName": {"type": ["string", "null"]},
            "priceCents": {"type": "integer"},
            "currency": {"type": "string"},
        },
        "required": ["name", "priceCents", "currency"],
    }

    sys_prompt = (
        "You extract structured product fields from a cashier's transcript.\n"
        "Return ONLY JSON matching the schema.\n"
        "Rules:\n"
        "- priceCents must be an integer >= 0.\n"
        "- currency must be a 3-letter code (default BDT).\n"
        "- Keep name <= 255 chars.\n"
        "- Keep sku <= 64 chars if present.\n"
        "- Keep barcode <= 64 chars if present.\n"
        "- Keep categoryName <= 255 chars if present.\n"
        "- description can be null.\n"
        f"Transcript:\n{transcript}"
    )

    result = await adapter.structured(
        messages=[Message(role="system", content=sys_prompt)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=400,
    )

    name = str(result.get("name", "")).strip()
    if not name:
        raise ValidationError("AI could not extract a product name.")

    price = result.get("priceCents", 0)
    try:
        price_cents = int(price)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("AI returned invalid price.") from exc

    currency = str(result.get("currency", "BDT")).strip().upper()[:3] or "BDT"
    draft = VoiceProductDraft(
        sku=(str(result.get("sku")).strip()[:64] if result.get("sku") else None),
        barcode=(str(result.get("barcode")).strip()[:64] if result.get("barcode") else None),
        name=name[:255],
        description=(str(result.get("description")).strip()[:1200] if result.get("description") else None),
        category_name=(str(result.get("categoryName")).strip()[:255] if result.get("categoryName") else None),
        price_cents=max(0, price_cents),
        currency=currency,
    )

    # Validate it can round-trip through existing update schema constraints (types/fields).
    _ = ProductUpdate(
        name=draft.name,
        description=draft.description,
        price_cents=draft.price_cents,
        currency=draft.currency,
    )
    return draft

