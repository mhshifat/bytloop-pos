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
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/ai/jewelry", tags=["ai-jewelry"])


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class PhotoEstimateRequest(CamelModel):
    asset: UploadedAsset


class PhotoEstimateResponse(CamelModel):
    karat: int | None = Field(default=None, ge=1, le=24)
    gross_grams: str | None = None
    net_grams: str | None = None


@router.post(
    "/photo-estimate",
    response_model=PhotoEstimateResponse,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def photo_estimate(
    req: PhotoEstimateRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PhotoEstimateResponse:
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
            "karat": {"type": ["integer", "null"]},
            "grossGrams": {"type": ["string", "null"]},
            "netGrams": {"type": ["string", "null"]},
        },
        "required": ["karat", "grossGrams", "netGrams"],
    }
    sys = (
        "You extract jewelry attributes from OCR text.\n"
        "Return ONLY JSON.\n"
        "Rules:\n"
        "- If you see a karat stamp (e.g. 18K, 22K, 916, 750), map to karat (e.g. 916->22, 750->18).\n"
        "- If no weight is present, set grossGrams/netGrams to null.\n"
        "- If no karat is present, set karat to null.\n"
        "OCR text:\n"
        f"{text[:12000]}"
    )
    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=200,
    )

    karat = parsed.get("karat")
    try:
        k = int(karat) if karat is not None else None
    except Exception:  # noqa: BLE001
        k = None

    gross = parsed.get("grossGrams")
    net = parsed.get("netGrams")

    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return PhotoEstimateResponse(
        karat=k if k is None else max(1, min(24, k)),
        gross_grams=str(gross).strip() if isinstance(gross, str) and gross.strip() else None,
        net_grams=str(net).strip() if isinstance(net, str) and net.strip() else None,
    )

