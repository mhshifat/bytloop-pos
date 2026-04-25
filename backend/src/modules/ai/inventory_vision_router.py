from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import Field

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import ValidationError
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.integrations.media.cloudinary import destroy, fetch_ocr_text
from src.modules.catalog.service import CatalogService
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/ai/inventory", tags=["ai-inventory"])


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class ShelfAuditRequest(CamelModel):
    asset: UploadedAsset
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class ShelfLabelRow(CamelModel):
    sku_or_name: str = Field(min_length=1, max_length=255)
    label_price_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class ShelfMismatch(CamelModel):
    sku_or_name: str
    label_price_cents: int
    pos_price_cents: int | None
    currency: str
    product_id: str | None = None
    product_name: str | None = None
    product_sku: str | None = None


class ShelfAuditResponse(CamelModel):
    rows: list[ShelfLabelRow]
    mismatches: list[ShelfMismatch]


@router.post(
    "/shelf-label-audit",
    response_model=ShelfAuditResponse,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def shelf_label_audit(
    req: ShelfAuditRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ShelfAuditResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    text = await fetch_ocr_text(public_id=req.asset.public_id)
    if not text:
        raise ValidationError(
            "OCR text not available. Ensure Cloudinary OCR (adv_ocr) is enabled for this account."
        )

    schema = {
        "type": "object",
        "properties": {
            "currency": {"type": "string"},
            "labels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "skuOrName": {"type": "string"},
                        "labelPriceCents": {"type": "integer"},
                    },
                    "required": ["skuOrName", "labelPriceCents"],
                },
            },
        },
        "required": ["currency", "labels"],
    }

    sys = (
        "You extract shelf label prices from OCR text.\n"
        "Return ONLY JSON matching schema.\n"
        "Rules:\n"
        "- labelPriceCents is integer cents.\n"
        "- currency is a 3-letter code (default BDT).\n"
        "- skuOrName should be short and stable.\n"
        "OCR text:\n"
        f"{text[:12000]}"
    )
    if req.currency:
        sys += f"\nPreferred currency: {req.currency}"

    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=800,
    )

    currency = (
        str(parsed.get("currency") or req.currency or "BDT").strip().upper()[:3] or "BDT"
    )
    labels = parsed.get("labels") if isinstance(parsed, dict) else None
    if not isinstance(labels, list) or not labels:
        raise ValidationError("Couldn't extract any shelf labels.")

    catalog = CatalogService(db)
    out_rows: list[ShelfLabelRow] = []
    mismatches: list[ShelfMismatch] = []

    for it in labels[:200]:
        if not isinstance(it, dict):
            continue
        sku_or_name = str(it.get("skuOrName", "")).strip()
        if not sku_or_name:
            continue
        try:
            label_price = int(it.get("labelPriceCents", 0))
        except Exception:  # noqa: BLE001
            label_price = 0
        row = ShelfLabelRow(
            sku_or_name=sku_or_name[:255],
            label_price_cents=max(0, label_price),
            currency=currency,
        )
        out_rows.append(row)

        rows, _ = await catalog.list_products(
            tenant_id=user.tenant_id, search=sku_or_name, category_id=None, page=1, page_size=5
        )
        match = None
        for p in rows:
            if p.sku.lower() == sku_or_name.lower():
                match = p
                break
        if match is None and rows:
            match = rows[0]

        pos_price = match.price_cents if match else None
        if pos_price is None or int(pos_price) != int(row.label_price_cents):
            mismatches.append(
                ShelfMismatch(
                    sku_or_name=row.sku_or_name,
                    label_price_cents=row.label_price_cents,
                    pos_price_cents=int(pos_price) if pos_price is not None else None,
                    currency=row.currency,
                    product_id=str(match.id) if match else None,
                    product_name=match.name if match else None,
                    product_sku=match.sku if match else None,
                )
            )

    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return ShelfAuditResponse(rows=out_rows, mismatches=mismatches)

