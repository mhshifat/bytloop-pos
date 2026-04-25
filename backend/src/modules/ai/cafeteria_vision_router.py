from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import Field

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import ValidationError
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.integrations.media.cloudinary import destroy, fetch_tags
from src.modules.catalog.service import CatalogService
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/ai/cafeteria", tags=["ai-cafeteria"])


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class PlateScanRequest(CamelModel):
    asset: UploadedAsset
    max_items: int = Field(default=5, ge=1, le=10)


class PlateLineDraft(CamelModel):
    product_id: str
    name: str
    quantity: int = Field(default=1, ge=1, le=20)
    unit_price_cents: int
    currency: str


class PlateScanResponse(CamelModel):
    tags: list[str]
    lines: list[PlateLineDraft]


@router.post(
    "/plate-scan",
    response_model=PlateScanResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def plate_scan(
    req: PlateScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PlateScanResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    tags = await fetch_tags(public_id=req.asset.public_id)
    if not tags:
        raise ValidationError(
            "Auto-tagging not available. Ensure Cloudinary categorization (google_tagging) is enabled."
        )

    schema = {
        "type": "object",
        "properties": {
            "queries": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["queries"],
    }
    sys = (
        "You suggest cafeteria menu items based on image tags.\n"
        "Return ONLY JSON.\n"
        "Rules:\n"
        "- Output 1-5 short search queries (e.g. 'chicken curry', 'salad', 'rice').\n"
        "- Prefer food items that are likely on a cafeteria menu.\n"
        f"Tags: {', '.join(tags[:30])}"
    )
    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.2,
        max_tokens=200,
    )
    queries_raw = parsed.get("queries") if isinstance(parsed, dict) else None
    if not isinstance(queries_raw, list) or not queries_raw:
        raise ValidationError("Could not infer any menu items.")

    catalog = CatalogService(db)
    lines: list[PlateLineDraft] = []
    seen: set[str] = set()
    for q in queries_raw[: req.max_items]:
        query = str(q).strip()
        if not query:
            continue
        rows, _ = await catalog.list_products(
            tenant_id=user.tenant_id, search=query, category_id=None, page=1, page_size=3
        )
        if not rows:
            continue
        p = rows[0]
        if str(p.id) in seen:
            continue
        seen.add(str(p.id))
        lines.append(
            PlateLineDraft(
                product_id=str(p.id),
                name=p.name,
                quantity=1,
                unit_price_cents=p.price_cents,
                currency=p.currency,
            )
        )

    if not lines:
        raise ValidationError("No matching products found in your catalog for the detected tags.")

    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return PlateScanResponse(tags=tags[:30], lines=lines)

