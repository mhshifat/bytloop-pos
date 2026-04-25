"""Procurement service — suppliers + purchase orders + receive to inventory.

Receiving writes both inventory movements (through InventoryService) and
updates the PO line received quantities — all within the request transaction.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from src.core.errors import ConflictError, NotFoundError
from src.modules.audit.api import AuditService
from src.modules.inventory.api import InventoryService
from src.modules.procurement.entity import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Supplier,
)
from src.modules.procurement.repository import (
    PurchaseOrderRepository,
    SupplierRepository,
)
from src.modules.procurement.schemas import (
    PurchaseOrderCreate,
    ReceiveItemInput,
    SupplierCreate,
)


class ProcurementService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        suppliers: SupplierRepository | None = None,
        purchase_orders: PurchaseOrderRepository | None = None,
        inventory: InventoryService | None = None,
    ) -> None:
        self._session = session
        self._suppliers = suppliers or SupplierRepository(session)
        self._pos = purchase_orders or PurchaseOrderRepository(session)
        self._inventory = inventory or InventoryService(session)
        self._audit = AuditService(session)

    # Suppliers
    async def list_suppliers(self, *, tenant_id: UUID) -> list[Supplier]:
        return await self._suppliers.list(tenant_id=tenant_id)

    async def create_supplier(
        self, *, tenant_id: UUID, actor_id: UUID | None, data: SupplierCreate
    ) -> Supplier:
        supplier = await self._suppliers.add(
            Supplier(
                tenant_id=tenant_id,
                code=data.code.upper(),
                name=data.name,
                email=data.email.lower() if data.email else None,
                phone=data.phone,
                notes=data.notes,
            )
        )
        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="supplier.created",
            resource_type="supplier",
            resource_id=str(supplier.id),
            after={"code": supplier.code, "name": supplier.name},
        )
        return supplier

    # Purchase orders
    async def list_purchase_orders(
        self, *, tenant_id: UUID, page: int, page_size: int
    ) -> tuple[list[PurchaseOrder], bool]:
        offset = max(0, (page - 1) * page_size)
        return await self._pos.list(tenant_id=tenant_id, limit=page_size, offset=offset)

    async def create_purchase_order(
        self, *, tenant_id: UUID, actor_id: UUID | None, data: PurchaseOrderCreate
    ) -> tuple[PurchaseOrder, list[PurchaseOrderItem]]:
        total = sum(i.quantity_ordered * i.unit_cost_cents for i in data.items)

        po = PurchaseOrder(
            tenant_id=tenant_id,
            supplier_id=data.supplier_id,
            number=f"PO-{str(ULID())[-10:]}",
            status=PurchaseOrderStatus.DRAFT,
            total_cents=total,
            currency=data.currency.upper(),
            sent_at=None,
            closed_at=None,
        )
        await self._pos.add(po)

        items = [
            PurchaseOrderItem(
                tenant_id=tenant_id,
                purchase_order_id=po.id,
                product_id=i.product_id,
                quantity_ordered=i.quantity_ordered,
                quantity_received=0,
                unit_cost_cents=i.unit_cost_cents,
                line_total_cents=i.quantity_ordered * i.unit_cost_cents,
            )
            for i in data.items
        ]
        await self._pos.add_items(items)

        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="purchase_order.created",
            resource_type="purchase_order",
            resource_id=str(po.id),
            after={"number": po.number, "total_cents": po.total_cents},
        )
        return po, items

    async def get_purchase_order(
        self, *, tenant_id: UUID, purchase_order_id: UUID
    ) -> tuple[PurchaseOrder, list[PurchaseOrderItem]]:
        po = await self._pos.get(tenant_id=tenant_id, purchase_order_id=purchase_order_id)
        if po is None:
            raise NotFoundError("Purchase order not found.")
        items = await self._pos.list_items(purchase_order_id=po.id)
        return po, items

    async def receive(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID | None,
        purchase_order_id: UUID,
        received: list[ReceiveItemInput],
    ) -> PurchaseOrder:
        po, items = await self.get_purchase_order(
            tenant_id=tenant_id, purchase_order_id=purchase_order_id
        )
        if po.status in {PurchaseOrderStatus.CANCELLED, PurchaseOrderStatus.RECEIVED}:
            raise ConflictError("This purchase order is already closed.")

        items_by_id = {i.id: i for i in items}
        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)

        for incoming in received:
            item = items_by_id.get(incoming.item_id)
            if item is None:
                raise NotFoundError("Line item doesn't belong to this purchase order.")
            remaining = item.quantity_ordered - item.quantity_received
            if incoming.quantity > remaining:
                raise ConflictError(
                    f"Tried to receive {incoming.quantity} but only {remaining} are outstanding."
                )
            item.quantity_received += incoming.quantity
            await self._inventory.receive_stock(
                tenant_id=tenant_id,
                product_id=item.product_id,
                location_id=location_id,
                quantity=incoming.quantity,
            )

        # Close if everything landed.
        all_received = all(i.quantity_received >= i.quantity_ordered for i in items)
        any_received = any(i.quantity_received > 0 for i in items)
        if all_received:
            po.status = PurchaseOrderStatus.RECEIVED
            po.closed_at = datetime.now(tz=UTC)
        elif any_received:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED

        await self._session.flush()

        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="purchase_order.received",
            resource_type="purchase_order",
            resource_id=str(po.id),
            after={"status": po.status.value},
        )
        return po
