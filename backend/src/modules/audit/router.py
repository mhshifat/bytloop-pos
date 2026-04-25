from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.audit.schemas import AuditEventList, AuditEventRead
from src.modules.audit.service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "",
    response_model=AuditEventList,
    dependencies=[Depends(requires(Permission.AUDIT_VIEW))],
)
async def list_events(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    resource_type: str | None = Query(default=None, alias="resourceType"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200, alias="pageSize"),
) -> AuditEventList:
    offset = max(0, (page - 1) * page_size)
    items, has_more = await AuditService(db).list(
        tenant_id=user.tenant_id,
        resource_type=resource_type,
        limit=page_size,
        offset=offset,
    )
    return AuditEventList(
        items=[AuditEventRead.model_validate(i) for i in items],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )
