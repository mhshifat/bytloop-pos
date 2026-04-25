from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.tax.schemas import TaxRuleCreate, TaxRuleRead
from src.modules.tax.service import TaxService

router = APIRouter(prefix="/tax-rules", tags=["tax"])


@router.get("", response_model=list[TaxRuleRead], dependencies=[Depends(requires(Permission.PRODUCTS_READ))])
async def list_tax_rules(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[TaxRuleRead]:
    rows = await TaxService(db).list_active(tenant_id=user.tenant_id)
    return [TaxRuleRead.model_validate(r) for r in rows]


@router.post(
    "",
    response_model=TaxRuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_tax_rule(
    data: TaxRuleCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TaxRuleRead:
    rule = await TaxService(db).create(tenant_id=user.tenant_id, data=data)
    return TaxRuleRead.model_validate(rule)
