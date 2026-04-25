from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import Field

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.modules.catalog.service import CatalogService

router = APIRouter(prefix="/personalization", tags=["personalization"])


class GiftRecommendRequest(CamelModel):
    prompt: str = Field(min_length=1, max_length=800)
    budget_cents: int = Field(ge=0, alias="budgetCents")
    currency: str = Field(min_length=3, max_length=3)
    vertical_hint: str | None = Field(default=None, alias="verticalHint", max_length=64)


class GiftRecommendItem(CamelModel):
    product_id: UUID = Field(alias="productId")
    rationale: str


class GiftRecommendResponse(CamelModel):
    products: list[GiftRecommendItem]


@router.post(
    "/gift-recommendations",
    response_model=GiftRecommendResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def gift_recommendations(
    req: GiftRecommendRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> GiftRecommendResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    # Candidate set: a small catalog slice by search over the prompt keywords.
    # MVP: use the prompt directly as search and take first 30 items.
    candidates, _ = await CatalogService(db).list_products(
        tenant_id=user.tenant_id,
        search=req.prompt,
        category_id=None,
        page=1,
        page_size=30,
    )
    # If no matches, fall back to generic list.
    if not candidates:
        candidates, _ = await CatalogService(db).list_products(
            tenant_id=user.tenant_id, search=None, category_id=None, page=1, page_size=30
        )

    catalog_context = [
        {
            "productId": str(p.id),
            "name": p.name,
            "priceCents": p.price_cents,
            "currency": p.currency,
        }
        for p in candidates
        if p.currency.upper() == req.currency.upper() or req.currency.upper() == ""
    ]

    schema = {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "productId": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["productId", "rationale"],
                },
            }
        },
        "required": ["products"],
    }

    sys = (
        "You recommend gifts from a POS catalog.\n"
        "Return ONLY JSON with up to 3 products.\n"
        "Rules:\n"
        "- Choose ONLY from the provided candidate list.\n"
        "- Keep rationale 1 sentence.\n"
        f"- Budget: {req.currency} {req.budget_cents/100:.2f}\n"
        f"- Prompt: {req.prompt}\n"
        f"Candidates: {catalog_context}\n"
    )
    result = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.4,
        max_tokens=300,
    )

    products = []
    seen: set[str] = set()
    for it in (result.get("products") or [])[:3]:
        if not isinstance(it, dict):
            continue
        pid = str(it.get("productId") or "").strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        rationale = str(it.get("rationale") or "").strip()[:300] or "Good match for the request."
        products.append(GiftRecommendItem(productId=UUID(pid), rationale=rationale))
    return GiftRecommendResponse(products=products)


class PairingsRequest(CamelModel):
    food_product_id: UUID = Field(alias="foodProductId")


class PairingsResponse(CamelModel):
    suggested_drink_product_ids: list[UUID] = Field(alias="suggestedDrinkProductIds")
    rationale: str


@router.post(
    "/pairings",
    response_model=PairingsResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def pairings(
    req: PairingsRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PairingsResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    food = await CatalogService(db).get_product(tenant_id=user.tenant_id, product_id=req.food_product_id)

    # Candidate drinks: best-effort search over common drink keywords.
    candidates: list[object] = []
    for q in ("wine", "beer", "cola", "juice", "water", "tea", "coffee"):
        items, _ = await CatalogService(db).list_products(
            tenant_id=user.tenant_id, search=q, category_id=None, page=1, page_size=10
        )
        candidates.extend(items)
        if len(candidates) >= 35:
            break
    if not candidates:
        items, _ = await CatalogService(db).list_products(
            tenant_id=user.tenant_id, search=None, category_id=None, page=1, page_size=30
        )
        candidates = list(items)

    uniq: dict[str, object] = {}
    for p in candidates:
        uniq[str(p.id)] = p
    candidates2 = list(uniq.values())[:30]

    catalog_context = [
        {"productId": str(p.id), "name": p.name, "priceCents": p.price_cents, "currency": p.currency}
        for p in candidates2
        if p.id != food.id
    ]

    schema = {
        "type": "object",
        "properties": {
            "suggestedDrinkProductIds": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": ["suggestedDrinkProductIds", "rationale"],
    }
    sys = (
        "You suggest drink pairings for a restaurant POS.\n"
        "Return ONLY JSON.\n"
        "- Choose ONLY from provided candidates.\n"
        "- Return up to 3 productIds.\n"
        f"Food item: {food.name}\n"
        f"Candidates: {catalog_context}\n"
    )
    result = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.3,
        max_tokens=250,
    )
    ids: list[UUID] = []
    for s in (result.get("suggestedDrinkProductIds") or [])[:3]:
        try:
            ids.append(UUID(str(s)))
        except Exception:  # noqa: BLE001
            continue
    rationale = str(result.get("rationale") or "").strip()[:300] or "Suggested drinks that complement the dish."
    return PairingsResponse(suggestedDrinkProductIds=ids, rationale=rationale)

