from __future__ import annotations

from datetime import date

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

router = APIRouter(prefix="/ai/age-restricted", tags=["ai-age-restricted"])


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class IdScanRequest(CamelModel):
    asset: UploadedAsset


class IdScanResponse(CamelModel):
    customer_dob: str


@router.post(
    "/id-scan",
    response_model=IdScanResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def id_scan(
    req: IdScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> IdScanResponse:
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
        "properties": {"customerDob": {"type": "string"}},
        "required": ["customerDob"],
    }
    sys = (
        "Extract the customer's date of birth from OCR text of an ID document.\n"
        "Return ONLY JSON matching schema.\n"
        "Rules:\n"
        "- Output customerDob in ISO format YYYY-MM-DD.\n"
        "- If multiple dates exist, choose the DOB (not issue/expiry).\n"
        "OCR text:\n"
        f"{text[:12000]}"
    )

    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=200,
    )
    dob_raw = str(parsed.get("customerDob", "")).strip()
    try:
        dob = date.fromisoformat(dob_raw)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("Couldn't extract a valid date of birth.") from exc

    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return IdScanResponse(customer_dob=dob.isoformat())

