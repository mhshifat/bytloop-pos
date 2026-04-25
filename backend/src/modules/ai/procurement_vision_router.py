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
from src.modules.procurement.repository import SupplierRepository
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/ai/procurement", tags=["ai-procurement"])


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class InvoiceOcrRequest(CamelModel):
    asset: UploadedAsset
    supplier_hint: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class InvoiceLineDraft(CamelModel):
    sku_or_name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, le=100000)
    unit_cost_cents: int = Field(ge=0)
    product_id: str | None = None


class PurchaseOrderDraft(CamelModel):
    supplier_id: str | None = None
    supplier_name: str | None = None
    currency: str = Field(min_length=3, max_length=3)
    lines: list[InvoiceLineDraft]


@router.post(
    "/invoice-ocr",
    response_model=PurchaseOrderDraft,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def invoice_ocr(
    req: InvoiceOcrRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PurchaseOrderDraft:
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
            "supplierName": {"type": ["string", "null"]},
            "currency": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "skuOrName": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "unitCostCents": {"type": "integer"},
                    },
                    "required": ["skuOrName", "quantity", "unitCostCents"],
                },
            },
        },
        "required": ["currency", "items"],
    }

    sys = (
        "You extract purchase-order line items from supplier invoices.\n"
        "Return ONLY JSON matching schema.\n"
        "Rules:\n"
        "- unitCostCents is the unit price in cents (integer).\n"
        "- quantity is an integer.\n"
        "- currency is a 3-letter code (default BDT unless invoice clearly indicates otherwise).\n"
        "- Keep skuOrName short.\n"
    )
    if req.supplier_hint:
        sys += f"\nSupplier hint: {req.supplier_hint}"
    if req.currency:
        sys += f"\nPreferred currency: {req.currency}"
    sys += f"\nInvoice text:\n{text[:12000]}"

    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=800,
    )

    supplier_name = (
        str(parsed.get("supplierName")).strip() if parsed.get("supplierName") else None
    )
    currency = (
        str(parsed.get("currency") or req.currency or "BDT").strip().upper()[:3] or "BDT"
    )
    raw_items = parsed.get("items") if isinstance(parsed, dict) else None
    if not isinstance(raw_items, list) or len(raw_items) == 0:
        raise ValidationError("Couldn't extract any line items from the invoice.")

    # Resolve supplier by name (best-effort).
    supplier_id: str | None = None
    if supplier_name:
        suppliers = await SupplierRepository(db).list(tenant_id=user.tenant_id)
        sn = supplier_name.lower()
        for s in suppliers:
            if s.name.lower() == sn:
                supplier_id = str(s.id)
                break

    # Resolve products by SKU (exact) or name search (best-effort).
    lines: list[InvoiceLineDraft] = []
    catalog = CatalogService(db)
    for it in raw_items[:80]:
        if not isinstance(it, dict):
            continue
        sku_or_name = str(it.get("skuOrName", "")).strip()
        if not sku_or_name:
            continue
        try:
            qty = int(it.get("quantity", 1))
        except Exception:  # noqa: BLE001
            qty = 1
        try:
            unit = int(it.get("unitCostCents", 0))
        except Exception:  # noqa: BLE001
            unit = 0

        product_id: str | None = None
        # Try SKU exact match by scanning first page with search.
        rows, _ = await catalog.list_products(
            tenant_id=user.tenant_id, search=sku_or_name, category_id=None, page=1, page_size=5
        )
        for p in rows:
            if p.sku.lower() == sku_or_name.lower():
                product_id = str(p.id)
                break
        if product_id is None and rows:
            product_id = str(rows[0].id)

        lines.append(
            InvoiceLineDraft(
                sku_or_name=sku_or_name[:255],
                quantity=max(1, qty),
                unit_cost_cents=max(0, unit),
                product_id=product_id,
            )
        )

    if not lines:
        raise ValidationError("Couldn't extract any usable line items.")

    # Respect per-tenant retention: if tenant opted for delete-after-processing, delete the asset.
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return PurchaseOrderDraft(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        currency=currency,
        lines=lines,
    )

