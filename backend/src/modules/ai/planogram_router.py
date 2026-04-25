from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select

from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import NotFoundError, ValidationError
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.integrations.media.cloudinary import destroy, fetch_ocr_text
from src.modules.inventory.planogram_entity import Planogram, PlanogramScan
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/ai/planograms", tags=["ai-planograms"])


class PlanogramCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    location_name: str | None = Field(default=None, max_length=255)
    expected_skus: list[str] = Field(min_length=1, max_length=300)


class PlanogramRead(CamelModel):
    id: UUID
    name: str
    location_name: str
    expected_skus: list[str]
    created_at: str


@router.get("", response_model=list[PlanogramRead], dependencies=[Depends(requires(Permission.PRODUCTS_READ))])
async def list_planograms(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PlanogramRead]:
    rows = list(
        (await db.execute(select(Planogram).where(Planogram.tenant_id == user.tenant_id))).scalars().all()
    )
    out: list[PlanogramRead] = []
    for p in rows:
        expected = p.expected if isinstance(p.expected, dict) else {}
        skus = expected.get("expectedSkus") if isinstance(expected, dict) else None
        out.append(
            PlanogramRead(
                id=p.id,
                name=p.name,
                location_name=p.location_name,
                expected_skus=[str(s).strip() for s in (skus or []) if str(s).strip()],
                created_at=p.created_at.isoformat(),
            )
        )
    return out


@router.post("", response_model=PlanogramRead, dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))])
async def create_planogram(
    data: PlanogramCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PlanogramRead:
    expected = {"expectedSkus": [s.strip()[:64] for s in data.expected_skus if s.strip()][:300]}
    row = Planogram(
        tenant_id=user.tenant_id,
        name=data.name,
        location_name=(data.location_name or "").strip()[:255],
        expected=expected,
    )
    db.add(row)
    await db.flush()
    return PlanogramRead(
        id=row.id,
        name=row.name,
        location_name=row.location_name,
        expected_skus=expected["expectedSkus"],
        created_at=row.created_at.isoformat(),
    )


class UploadedAsset(CamelModel):
    public_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=1024)


class PlanogramScanRequest(CamelModel):
    asset: UploadedAsset
    planogram_id: UUID | None = None


class PlanogramScanResponse(CamelModel):
    scan_id: UUID
    expected_skus: list[str]
    detected_skus: list[str]
    missing_skus: list[str]
    unexpected_skus: list[str]


@router.post("/scan", response_model=PlanogramScanResponse, dependencies=[Depends(requires(Permission.PRODUCTS_READ))])
async def scan_planogram(
    req: PlanogramScanRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PlanogramScanResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    expected_skus: list[str] = []
    planogram_id = req.planogram_id
    if planogram_id is not None:
        p = (
            await db.execute(
                select(Planogram).where(Planogram.id == planogram_id, Planogram.tenant_id == user.tenant_id)
            )
        ).scalar_one_or_none()
        if p is None:
            raise NotFoundError("Planogram not found.")
        expected = p.expected if isinstance(p.expected, dict) else {}
        skus = expected.get("expectedSkus") if isinstance(expected, dict) else None
        expected_skus = [str(s).strip() for s in (skus or []) if str(s).strip()]

    text = await fetch_ocr_text(public_id=req.asset.public_id)
    if not text:
        raise ValidationError(
            "OCR text not available. Ensure Cloudinary OCR (adv_ocr) is enabled for this account."
        )

    schema = {
        "type": "object",
        "properties": {"detectedSkus": {"type": "array", "items": {"type": "string"}}},
        "required": ["detectedSkus"],
    }
    sys = (
        "Extract product SKUs from shelf OCR text.\n"
        "Return ONLY JSON.\n"
        "Rules:\n"
        "- Only include strings that look like SKUs (letters/numbers/dashes).\n"
        "- Deduplicate.\n"
        f"OCR text:\n{text[:12000]}"
    )
    parsed = await adapter.structured(
        messages=[Message(role="system", content=sys)],
        json_schema=schema,
        temperature=0.1,
        max_tokens=300,
    )
    det = parsed.get("detectedSkus")
    detected_skus = []
    if isinstance(det, list):
        seen: set[str] = set()
        for s in det:
            t = str(s).strip()[:64]
            if not t:
                continue
            key = t.upper()
            if key in seen:
                continue
            seen.add(key)
            detected_skus.append(t)

    expected_set = {s.upper() for s in expected_skus}
    detected_set = {s.upper() for s in detected_skus}
    missing = [s for s in expected_skus if s.upper() not in detected_set]
    unexpected = [s for s in detected_skus if s.upper() not in expected_set] if expected_skus else []

    scan = PlanogramScan(
        tenant_id=user.tenant_id,
        planogram_id=planogram_id,
        image_public_id=req.asset.public_id,
        result={
            "expectedSkus": expected_skus,
            "detectedSkus": detected_skus,
            "missingSkus": missing,
            "unexpectedSkus": unexpected,
            "generatedAt": datetime.now(tz=UTC).isoformat(),
        },
    )
    db.add(scan)
    await db.flush()

    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    tcfg = dict(tenant.config or {}) if tenant else {}
    retention = str(tcfg.get("aiMediaRetention") or "delete_after_processing")
    if retention == "delete_after_processing":
        await destroy(public_id=req.asset.public_id)

    return PlanogramScanResponse(
        scan_id=scan.id,
        expected_skus=expected_skus,
        detected_skus=detected_skus,
        missing_skus=missing,
        unexpected_skus=unexpected,
    )

