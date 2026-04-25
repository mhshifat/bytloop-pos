from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import Field

from src.core import cache
from src.core.deps import DbSession, get_current_user, requires
from src.core.errors import ValidationError
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.integrations.media.cloudinary import MAX_UPLOAD_BYTES, is_configured, signed_direct_upload
from src.modules.tenants.repository import TenantRepository

router = APIRouter(prefix="/media", tags=["media"])


class UploadSignRequest(CamelModel):
    purpose: str = Field(min_length=1, max_length=32)
    content_type: str = Field(min_length=1, max_length=128)
    bytes: int = Field(ge=1)


class UploadSignResponse(CamelModel):
    upload_url: str
    fields: dict[str, str]
    public_id: str
    max_bytes: int


def _client_ip(request: Request) -> str:
    real = getattr(request.state, "real_ip", None)
    if isinstance(real, str) and real:
        return real
    if request.client:
        return request.client.host
    return "unknown"


async def _rate_limit_ok(*, tenant_id: str, ip: str) -> bool:
    """Sign endpoint abuse guard: 120/min per tenant+ip. Redis down = fail open."""
    key = f"pos:rl:upload_sign:{tenant_id}:{ip}"
    raw = await cache.get_str(key)
    count = int(raw) if raw and raw.isdigit() else 0
    if count >= 120:
        return False
    await cache.set_str(key, str(count + 1), ttl_seconds=60)
    return True


@router.post(
    "/uploads/sign",
    response_model=UploadSignResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def sign_upload(
    req: UploadSignRequest,
    request: Request,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> UploadSignResponse:
    if not is_configured():
        raise ValidationError("Media uploads are not configured.")

    if req.bytes > MAX_UPLOAD_BYTES:
        raise ValidationError(f"File too large (max {MAX_UPLOAD_BYTES} bytes).")

    if not req.content_type.lower().startswith("image/"):
        raise ValidationError("Only image uploads are supported.")

    ip = _client_ip(request)
    if not await _rate_limit_ok(tenant_id=str(user.tenant_id), ip=ip):
        raise ValidationError("Too many requests. Please wait and try again.")

    # Retention policy is per-tenant; we tag for later cleanup if not ephemeral.
    tenant = await TenantRepository(db).get_by_id(user.tenant_id)
    config = dict(tenant.config or {}) if tenant else {}
    retention = str(config.get("aiMediaRetention") or "delete_after_processing")
    tags = [f"tenant_{user.tenant_id}", f"purpose_{req.purpose}"]
    if retention != "delete_after_processing":
        tags.append("retention_managed")
        tags.append(f"retention_{retention}")

    public_id = f"{user.tenant_id}/{req.purpose}/{user.id}"
    signed = signed_direct_upload(folder=f"bytloop/{user.tenant_id}/{req.purpose}", public_id=public_id, tags=tags)
    return UploadSignResponse(
        upload_url=signed.upload_url,
        fields=signed.fields,
        public_id=signed.public_id,
        max_bytes=MAX_UPLOAD_BYTES,
    )

