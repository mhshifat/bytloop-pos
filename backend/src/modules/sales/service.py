"""Sales service — cash checkout happy path.

Single transaction: create order + items + payment + decrement inventory.
If anything fails the whole thing rolls back — docs/PLAN.md §15b.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, ValidationError
from src.modules.audit.api import AuditService
from src.modules.catalog.api import CatalogService
from src.modules.inventory.api import InventoryService
from src.modules.sales.entity import (
    Order,
    OrderItem,
    OrderStatus,
    OrderType,
    Payment,
    PaymentMethod,
)
from src.modules.sales.repository import OrderRepository
from src.modules.sales.schemas import (
    AgeVerificationCheckout,
    CartItemInput,
)
from src.modules.tenants.entity import Tenant, VerticalProfile
from src.verticals.retail.age_restricted.service import AgeRestrictedService
from src.verticals.retail.electronics.service import ElectronicsService
from src.verticals.retail.hardware.service import HardwareService


@dataclass(slots=True)
class CompletedSale:
    order: Order
    items: list[OrderItem]
    payments: list[Payment]
    change_due_cents: int


class SalesService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        catalog: CatalogService | None = None,
        inventory: InventoryService | None = None,
        orders: OrderRepository | None = None,
    ) -> None:
        self._session = session
        self._catalog = catalog or CatalogService(session)
        self._inventory = inventory or InventoryService(session)
        self._orders = orders or OrderRepository(session)

    async def checkout(
        self,
        *,
        tenant_id: UUID,
        cashier_id: UUID,
        items: list[CartItemInput],
        order_type: OrderType,
        payment_method: PaymentMethod,
        amount_tendered_cents: int | None,
        customer_id: UUID | None = None,
        discount_code: str | None = None,
        payment_reference: str | None = None,
        order_vertical_data: dict[str, Any] | None = None,
        age_verification: AgeVerificationCheckout | None = None,
    ) -> CompletedSale:
        if not items:
            raise ValidationError("Cart is empty.")

        tenant = await self._session.get(Tenant, tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found.")
        profile: VerticalProfile = tenant.vertical_profile

        age_gated = await AgeRestrictedService(self._session).requires_verification(
            tenant_id=tenant_id, product_ids=[i.product_id for i in items]
        )
        if age_gated and age_verification is None:
            raise ValidationError(
                "This sale includes age-restricted products. Provide date of birth in ageVerification."
            )

        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)

        merged_vdata: dict[str, Any] = {**(order_vertical_data or {})}
        merged_vdata["verticalProfile"] = profile.value

        order = Order(
            tenant_id=tenant_id,
            location_id=location_id,
            cashier_id=cashier_id,
            customer_id=customer_id,
            number=_order_number(),
            order_type=order_type,
            status=OrderStatus.OPEN,
            currency="BDT",
            vertical_data=merged_vdata,
        )
        await self._orders.add(order)

        order_items: list[OrderItem] = []
        subtotal = 0
        tax = 0
        excise_total = 0

        hw = HardwareService(self._session) if profile == VerticalProfile.RETAIL_HARDWARE else None
        for line in items:
            product = await self._catalog.get_product(
                tenant_id=tenant_id, product_id=line.product_id
            )
            unit = product.price_cents
            if hw is not None:
                unit, _matched = await hw.resolve_unit_price(
                    tenant_id=tenant_id, product_id=line.product_id, quantity=line.quantity
                )
            line_subtotal = unit * line.quantity
            line_tax = int(line_subtotal * float(product.tax_rate))
            line_excise = 0
            if profile == VerticalProfile.RETAIL_LIQUOR and line.excise_cents is not None:
                line_excise = int(line.excise_cents)
            line_total = line_subtotal + line_tax + line_excise

            vdata: dict[str, Any] = dict(line.vertical_data or {})
            vdata.setdefault("lineExciseCents", line_excise)
            vdata.setdefault("unitPriceCents", unit)
            vdata.setdefault("retailListPriceCents", product.price_cents)

            order_items.append(
                OrderItem(
                    tenant_id=tenant_id,
                    order_id=order.id,
                    product_id=product.id,
                    name_snapshot=product.name,
                    unit_price_cents=unit,
                    quantity=line.quantity,
                    subtotal_cents=line_subtotal,
                    tax_cents=line_tax,
                    line_total_cents=line_total,
                    vertical_data=vdata,
                )
            )
            subtotal += line_subtotal
            tax += line_tax
            excise_total += line_excise

            if product.track_inventory:
                await self._inventory.consume_for_sale(
                    tenant_id=tenant_id,
                    product_id=product.id,
                    location_id=location_id,
                    quantity=line.quantity,
                    order_id=order.id,
                )

        await self._orders.add_items(order_items)

        if age_gated and age_verification is not None:
            pids: list[UUID] = (
                list(age_verification.product_ids)
                if age_verification.product_ids
                else [r["product_id"] for r in age_gated]
            )
            await AgeRestrictedService(self._session).record_verification(
                tenant_id=tenant_id,
                order_id=order.id,
                customer_dob=age_verification.customer_dob,
                verified_by_user_id=cashier_id,
                product_ids=pids,
            )

        for line in items:
            vd = line.vertical_data or {}
            eid = vd.get("electronicsItemId")
            sno = vd.get("serialNo")
            im = vd.get("imei")
            if eid or sno or im:
                try:
                    await ElectronicsService(self._session).mark_sold_for_line(
                        tenant_id=tenant_id,
                        product_id=line.product_id,
                        order_id=order.id,
                        item_id=UUID(str(eid)) if eid is not None else None,
                        serial_no=str(sno) if sno is not None else None,
                        imei=str(im) if im is not None else None,
                    )
                except (ValueError, TypeError):
                    raise ValidationError("Invalid electronicsItemId in cart line.") from None

        # Apply discount code (if any) against the pre-tax subtotal.
        discount_amount = 0
        if discount_code:
            from src.modules.discounts.api import DiscountService

            discount_amount = await DiscountService(self._session).resolve(
                tenant_id=tenant_id, code=discount_code, subtotal_cents=subtotal
            )

        order.vertical_data = {**order.vertical_data, "exciseCents": excise_total}
        order.subtotal_cents = subtotal
        order.tax_cents = tax
        order.discount_cents = discount_amount
        order.total_cents = max(0, subtotal + tax + excise_total - discount_amount)
        order.status = OrderStatus.COMPLETED
        order.closed_at = datetime.now(tz=UTC)

        tendered = amount_tendered_cents if amount_tendered_cents is not None else order.total_cents
        if tendered < order.total_cents:
            raise ValidationError("Amount tendered is less than total due.")

        payment = Payment(
            tenant_id=tenant_id,
            order_id=order.id,
            method=payment_method,
            amount_cents=order.total_cents,
            currency=order.currency,
            reference=payment_reference,
        )
        await self._orders.add_payment(payment)

        change_due = tendered - order.total_cents if payment_method == PaymentMethod.CASH else 0

        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=cashier_id,
            action="order.completed",
            resource_type="order",
            resource_id=str(order.id),
            after={
                "number": order.number,
                "total_cents": order.total_cents,
                "payment_method": payment_method.value,
                "item_count": len(order_items),
            },
        )

        # Emit domain event for plugins (no awaited Redis/IO on hot path).
        from src.core.events import canonical_payload, emit

        await emit(
            "order.completed",
            canonical_payload(
                tenant_id=tenant_id,
                actor_id=cashier_id,
                resource_id=str(order.id),
                extra={
                    "number": order.number,
                    "totalCents": order.total_cents,
                    "paymentMethod": payment_method.value,
                    "itemCount": len(order_items),
                },
            ),
        )

        return CompletedSale(
            order=order,
            items=order_items,
            payments=[payment],
            change_due_cents=change_due,
        )

    async def get_order(self, *, tenant_id: UUID, order_id: UUID) -> CompletedSale:
        order = await self._orders.get_with_relations(
            tenant_id=tenant_id, order_id=order_id
        )
        if order is None:
            raise NotFoundError("Order not found.")
        items = await self._orders.list_items(order_id=order.id)
        payments = await self._orders.list_payments(order_id=order.id)
        return CompletedSale(order=order, items=items, payments=payments, change_due_cents=0)

    async def list_orders(
        self,
        *,
        tenant_id: UUID,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
        since: "datetime | None" = None,
        until: "datetime | None" = None,
    ) -> tuple[list[Order], bool]:
        offset = max(0, (page - 1) * page_size)
        return await self._orders.list(
            tenant_id=tenant_id,
            limit=page_size,
            offset=offset,
            status=status,
            since=since,
            until=until,
        )

    async def void_order(
        self, *, tenant_id: UUID, actor_id: UUID | None, order_id: UUID
    ) -> Order:
        sale = await self.get_order(tenant_id=tenant_id, order_id=order_id)
        order = sale.order
        if order.status != OrderStatus.COMPLETED:
            raise ValidationError("Only completed orders can be voided.")
        order.status = OrderStatus.VOIDED
        await self._return_stock(sale)
        await self._session.flush()
        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="order.voided",
            resource_type="order",
            resource_id=str(order.id),
        )
        return order

    async def refund_order(
        self, *, tenant_id: UUID, actor_id: UUID | None, order_id: UUID
    ) -> Order:
        sale = await self.get_order(tenant_id=tenant_id, order_id=order_id)
        order = sale.order
        if order.status != OrderStatus.COMPLETED:
            raise ValidationError("Only completed orders can be refunded.")
        order.status = OrderStatus.REFUNDED
        await self._return_stock(sale)
        await self._session.flush()
        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="order.refunded",
            resource_type="order",
            resource_id=str(order.id),
            after={"total_cents": order.total_cents},
        )
        return order

    async def _return_stock(self, sale: CompletedSale) -> None:
        for item in sale.items:
            product = await self._catalog.get_product(
                tenant_id=sale.order.tenant_id, product_id=item.product_id
            )
            if product.track_inventory:
                await self._inventory.receive_stock(
                    tenant_id=sale.order.tenant_id,
                    product_id=product.id,
                    location_id=sale.order.location_id,
                    quantity=item.quantity,
                )


def _order_number() -> str:
    from ulid import ULID

    return f"O-{str(ULID())[-10:]}"
