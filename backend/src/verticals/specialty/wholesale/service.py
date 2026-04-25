from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.modules.sales.api import Order
from src.verticals.specialty.wholesale.entity import (
    Invoice,
    InvoicePayment,
    InvoiceStatus,
    WholesaleCustomer,
    WholesaleTier,
)


class WholesaleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Tiers
    # ──────────────────────────────────────────────

    async def list_tiers(self, *, tenant_id: UUID) -> list[WholesaleTier]:
        stmt = (
            select(WholesaleTier)
            .where(WholesaleTier.tenant_id == tenant_id)
            .order_by(WholesaleTier.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def upsert_tier(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        discount_pct: Decimal,
    ) -> WholesaleTier:
        stmt = select(WholesaleTier).where(
            WholesaleTier.tenant_id == tenant_id,
            WholesaleTier.code == code,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.name = name
            existing.discount_pct = discount_pct
            await self._session.flush()
            return existing
        tier = WholesaleTier(
            tenant_id=tenant_id,
            code=code,
            name=name,
            discount_pct=discount_pct,
        )
        self._session.add(tier)
        await self._session.flush()
        return tier

    async def _get_tier(
        self, *, tenant_id: UUID, code: str
    ) -> WholesaleTier | None:
        stmt = select(WholesaleTier).where(
            WholesaleTier.tenant_id == tenant_id,
            WholesaleTier.code == code,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # ──────────────────────────────────────────────
    # Wholesale customers
    # ──────────────────────────────────────────────

    async def register_wholesale_customer(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        tier_code: str | None,
        credit_limit_cents: int,
        net_terms_days: int,
        tax_exempt: bool,
    ) -> WholesaleCustomer:
        if tier_code is not None:
            tier = await self._get_tier(tenant_id=tenant_id, code=tier_code)
            if tier is None:
                raise ValidationError(
                    f"Unknown wholesale tier '{tier_code}'. Create it first."
                )
        stmt = select(WholesaleCustomer).where(
            WholesaleCustomer.tenant_id == tenant_id,
            WholesaleCustomer.customer_id == customer_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            raise ConflictError(
                "This customer is already registered as a wholesale account."
            )
        wc = WholesaleCustomer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            tier_code=tier_code,
            credit_limit_cents=credit_limit_cents,
            credit_balance_cents=0,
            net_terms_days=net_terms_days,
            tax_exempt=tax_exempt,
        )
        self._session.add(wc)
        await self._session.flush()
        return wc

    async def list_wholesale_customers(
        self, *, tenant_id: UUID
    ) -> list[WholesaleCustomer]:
        stmt = (
            select(WholesaleCustomer)
            .where(WholesaleCustomer.tenant_id == tenant_id)
            .order_by(WholesaleCustomer.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_wholesale_customer(
        self, *, tenant_id: UUID, wholesale_customer_id: UUID
    ) -> WholesaleCustomer:
        wc = await self._session.get(WholesaleCustomer, wholesale_customer_id)
        if wc is None or wc.tenant_id != tenant_id:
            raise NotFoundError("Wholesale customer not found.")
        return wc

    # ──────────────────────────────────────────────
    # Pricing
    # ──────────────────────────────────────────────

    async def apply_tier_discount(
        self,
        *,
        tenant_id: UUID,
        wholesale_customer_id: UUID,
        subtotal_cents: int,
    ) -> dict[str, int | str | Decimal | None]:
        wc = await self.get_wholesale_customer(
            tenant_id=tenant_id, wholesale_customer_id=wholesale_customer_id
        )
        pct = Decimal(0)
        if wc.tier_code:
            tier = await self._get_tier(tenant_id=tenant_id, code=wc.tier_code)
            if tier is not None:
                pct = Decimal(tier.discount_pct)
        # Integer-cent rounding with banker's precision — floor the discount
        # so we never overcharge the customer vs. the posted percent.
        discount_cents = int((Decimal(subtotal_cents) * pct) / Decimal(100))
        discounted_cents = subtotal_cents - discount_cents
        return {
            "subtotal_cents": subtotal_cents,
            "discount_cents": discount_cents,
            "discounted_cents": discounted_cents,
            "tier_code": wc.tier_code,
            "discount_pct": pct,
        }

    # ──────────────────────────────────────────────
    # Invoices
    # ──────────────────────────────────────────────

    async def create_invoice(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        wholesale_customer_id: UUID,
        invoice_no: str,
        issued_on: date | None = None,
    ) -> Invoice:
        wc = await self.get_wholesale_customer(
            tenant_id=tenant_id, wholesale_customer_id=wholesale_customer_id
        )
        # Pull the order total via the sales public API (Order entity). Never
        # reach into sales.service/repository directly.
        order = await self._session.get(Order, order_id)
        if order is None or order.tenant_id != tenant_id:
            raise NotFoundError("Order not found.")
        amount_cents = int(order.total_cents)

        issued = issued_on or date.today()
        due = issued + timedelta(days=wc.net_terms_days)

        # Duplicate invoice_no guard — returns clean 409 instead of IntegrityError.
        dup_stmt = select(Invoice).where(
            Invoice.tenant_id == tenant_id, Invoice.invoice_no == invoice_no
        )
        if (await self._session.execute(dup_stmt)).scalar_one_or_none() is not None:
            raise ConflictError(
                f"Invoice number '{invoice_no}' already exists for this tenant."
            )

        # Credit-limit gate — project the new balance and refuse if it breaks
        # the cap. A zero limit means "no credit extended".
        projected = wc.credit_balance_cents + amount_cents
        if projected > wc.credit_limit_cents:
            raise ConflictError(
                "Invoice would exceed the customer's credit limit.",
                code="credit_limit_exceeded",
                details={
                    "credit_limit_cents": wc.credit_limit_cents,
                    "current_balance_cents": wc.credit_balance_cents,
                    "invoice_amount_cents": amount_cents,
                },
            )

        invoice = Invoice(
            tenant_id=tenant_id,
            wholesale_customer_id=wholesale_customer_id,
            order_id=order_id,
            invoice_no=invoice_no,
            issued_on=issued,
            due_on=due,
            status=InvoiceStatus.OPEN,
            amount_cents=amount_cents,
            paid_cents=0,
        )
        wc.credit_balance_cents = projected
        self._session.add(invoice)
        await self._session.flush()
        return invoice

    async def get_invoice(
        self, *, tenant_id: UUID, invoice_id: UUID
    ) -> Invoice:
        invoice = await self._session.get(Invoice, invoice_id)
        if invoice is None or invoice.tenant_id != tenant_id:
            raise NotFoundError("Invoice not found.")
        return invoice

    async def list_invoices(
        self, *, tenant_id: UUID, status: InvoiceStatus | None = None
    ) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(Invoice.status == status)
        stmt = stmt.order_by(Invoice.issued_on.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def record_payment(
        self,
        *,
        tenant_id: UUID,
        invoice_id: UUID,
        amount_cents: int,
        paid_on: date,
        reference: str | None = None,
    ) -> InvoicePayment:
        if amount_cents <= 0:
            raise ValidationError("Payment amount must be positive.")
        invoice = await self.get_invoice(tenant_id=tenant_id, invoice_id=invoice_id)
        if invoice.status == InvoiceStatus.WRITTEN_OFF:
            raise ConflictError("Cannot record payment against a written-off invoice.")
        remaining = invoice.amount_cents - invoice.paid_cents
        if amount_cents > remaining:
            raise ConflictError(
                f"Payment {amount_cents} exceeds remaining balance {remaining}."
            )

        wc = await self.get_wholesale_customer(
            tenant_id=tenant_id, wholesale_customer_id=invoice.wholesale_customer_id
        )
        invoice.paid_cents += amount_cents
        wc.credit_balance_cents -= amount_cents
        if invoice.paid_cents >= invoice.amount_cents:
            invoice.status = InvoiceStatus.PAID

        payment = InvoicePayment(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount_cents=amount_cents,
            paid_on=paid_on,
            reference=reference,
        )
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def list_payments(
        self, *, tenant_id: UUID, invoice_id: UUID
    ) -> list[InvoicePayment]:
        await self.get_invoice(tenant_id=tenant_id, invoice_id=invoice_id)
        stmt = (
            select(InvoicePayment)
            .where(
                InvoicePayment.tenant_id == tenant_id,
                InvoicePayment.invoice_id == invoice_id,
            )
            .order_by(InvoicePayment.paid_on.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def overdue_invoices(self, *, tenant_id: UUID) -> list[Invoice]:
        """Return open invoices past due_on. Flips them to OVERDUE as a
        side-effect so downstream reports see a consistent status."""
        today = date.today()
        stmt = (
            select(Invoice)
            .where(
                Invoice.tenant_id == tenant_id,
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]),
                Invoice.due_on < today,
            )
            .order_by(Invoice.due_on)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        for inv in rows:
            if inv.status == InvoiceStatus.OPEN:
                inv.status = InvoiceStatus.OVERDUE
        if rows:
            await self._session.flush()
        return rows
