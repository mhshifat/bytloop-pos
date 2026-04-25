from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.wholesale.entity import InvoiceStatus
from src.verticals.specialty.wholesale.schemas import (
    ApplyDiscountRequest,
    ApplyDiscountResponse,
    InvoiceCreate,
    InvoiceRead,
    PaymentCreate,
    PaymentRead,
    TierRead,
    TierUpsert,
    WholesaleCustomerCreate,
    WholesaleCustomerRead,
)
from src.verticals.specialty.wholesale.service import WholesaleService

router = APIRouter(prefix="/wholesale", tags=["wholesale"])


# ──────────────────────────────────────────────
# Tiers
# ──────────────────────────────────────────────


@router.get(
    "/tiers",
    response_model=list[TierRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_tiers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[TierRead]:
    rows = await WholesaleService(db).list_tiers(tenant_id=user.tenant_id)
    return [TierRead.model_validate(r) for r in rows]


@router.put(
    "/tiers",
    response_model=TierRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_tier(
    data: TierUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> TierRead:
    tier = await WholesaleService(db).upsert_tier(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        discount_pct=data.discount_pct,
    )
    return TierRead.model_validate(tier)


# ──────────────────────────────────────────────
# Wholesale customers
# ──────────────────────────────────────────────


@router.get(
    "/customers",
    response_model=list[WholesaleCustomerRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_wholesale_customers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[WholesaleCustomerRead]:
    rows = await WholesaleService(db).list_wholesale_customers(
        tenant_id=user.tenant_id
    )
    return [WholesaleCustomerRead.model_validate(r) for r in rows]


@router.post(
    "/customers",
    response_model=WholesaleCustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def register_wholesale_customer(
    data: WholesaleCustomerCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> WholesaleCustomerRead:
    wc = await WholesaleService(db).register_wholesale_customer(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        tier_code=data.tier_code,
        credit_limit_cents=data.credit_limit_cents,
        net_terms_days=data.net_terms_days,
        tax_exempt=data.tax_exempt,
    )
    return WholesaleCustomerRead.model_validate(wc)


@router.get(
    "/customers/{wholesale_customer_id}",
    response_model=WholesaleCustomerRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_wholesale_customer(
    wholesale_customer_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> WholesaleCustomerRead:
    wc = await WholesaleService(db).get_wholesale_customer(
        tenant_id=user.tenant_id,
        wholesale_customer_id=wholesale_customer_id,
    )
    return WholesaleCustomerRead.model_validate(wc)


# ──────────────────────────────────────────────
# Pricing
# ──────────────────────────────────────────────


@router.post(
    "/apply-discount",
    response_model=ApplyDiscountResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def apply_discount(
    data: ApplyDiscountRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ApplyDiscountResponse:
    result = await WholesaleService(db).apply_tier_discount(
        tenant_id=user.tenant_id,
        wholesale_customer_id=data.wholesale_customer_id,
        subtotal_cents=data.subtotal_cents,
    )
    return ApplyDiscountResponse.model_validate(result)


# ──────────────────────────────────────────────
# Invoices
# ──────────────────────────────────────────────


@router.get(
    "/invoices",
    response_model=list[InvoiceRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_invoices(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    status_filter: InvoiceStatus | None = Query(default=None, alias="status"),
) -> list[InvoiceRead]:
    rows = await WholesaleService(db).list_invoices(
        tenant_id=user.tenant_id, status=status_filter
    )
    return [InvoiceRead.model_validate(r) for r in rows]


@router.post(
    "/invoices",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_invoice(
    data: InvoiceCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> InvoiceRead:
    invoice = await WholesaleService(db).create_invoice(
        tenant_id=user.tenant_id,
        order_id=data.order_id,
        wholesale_customer_id=data.wholesale_customer_id,
        invoice_no=data.invoice_no,
        issued_on=data.issued_on,
    )
    return InvoiceRead.model_validate(invoice)


@router.get(
    "/invoices/overdue",
    response_model=list[InvoiceRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def overdue_invoices(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[InvoiceRead]:
    rows = await WholesaleService(db).overdue_invoices(tenant_id=user.tenant_id)
    return [InvoiceRead.model_validate(r) for r in rows]


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceRead,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def get_invoice(
    invoice_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> InvoiceRead:
    invoice = await WholesaleService(db).get_invoice(
        tenant_id=user.tenant_id, invoice_id=invoice_id
    )
    return InvoiceRead.model_validate(invoice)


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def record_payment(
    invoice_id: UUID,
    data: PaymentCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PaymentRead:
    payment = await WholesaleService(db).record_payment(
        tenant_id=user.tenant_id,
        invoice_id=invoice_id,
        amount_cents=data.amount_cents,
        paid_on=data.paid_on,
        reference=data.reference,
    )
    return PaymentRead.model_validate(payment)


@router.get(
    "/invoices/{invoice_id}/payments",
    response_model=list[PaymentRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_payments(
    invoice_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PaymentRead]:
    rows = await WholesaleService(db).list_payments(
        tenant_id=user.tenant_id, invoice_id=invoice_id
    )
    return [PaymentRead.model_validate(r) for r in rows]
