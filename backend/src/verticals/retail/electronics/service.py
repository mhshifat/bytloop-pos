from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.retail.electronics.entity import ElectronicsItem


def _days_between(today: date, target: date) -> int:
    return (target - today).days


def _warranty_expiry(purchased_on: date | None, warranty_months: int) -> date | None:
    if purchased_on is None or warranty_months <= 0:
        return None
    # Month arithmetic without pulling in dateutil: advance by months with a
    # clamp when the target month has fewer days.
    year = purchased_on.year + (purchased_on.month - 1 + warranty_months) // 12
    month = (purchased_on.month - 1 + warranty_months) % 12 + 1
    day = purchased_on.day
    # Clamp to last day of target month.
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
            if day < 1:
                return purchased_on


class ElectronicsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register_item(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        serial_no: str,
        imei: str | None = None,
        warranty_months: int = 0,
        purchased_on: date | None = None,
    ) -> ElectronicsItem:
        # Reject duplicate serial for the same tenant before the DB does, so
        # we get a clean ConflictError instead of IntegrityError bubbling up.
        existing = (
            await self._session.execute(
                select(ElectronicsItem).where(
                    ElectronicsItem.tenant_id == tenant_id,
                    ElectronicsItem.serial_no == serial_no,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("That serial number is already registered.")
        if imei is not None:
            imei_clash = (
                await self._session.execute(
                    select(ElectronicsItem).where(
                        ElectronicsItem.tenant_id == tenant_id,
                        ElectronicsItem.imei == imei,
                    )
                )
            ).scalar_one_or_none()
            if imei_clash is not None:
                raise ConflictError("That IMEI is already registered.")
        item = ElectronicsItem(
            tenant_id=tenant_id,
            product_id=product_id,
            serial_no=serial_no,
            imei=imei,
            warranty_months=warranty_months,
            purchased_on=purchased_on,
            sold_order_id=None,
            sold_at=None,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def lookup_by_serial(
        self, *, tenant_id: UUID, serial_no: str
    ) -> ElectronicsItem | None:
        stmt = select(ElectronicsItem).where(
            ElectronicsItem.tenant_id == tenant_id,
            ElectronicsItem.serial_no == serial_no,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def lookup_by_imei(
        self, *, tenant_id: UUID, imei: str
    ) -> ElectronicsItem | None:
        stmt = select(ElectronicsItem).where(
            ElectronicsItem.tenant_id == tenant_id,
            ElectronicsItem.imei == imei,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_product(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> list[ElectronicsItem]:
        stmt = (
            select(ElectronicsItem)
            .where(
                ElectronicsItem.tenant_id == tenant_id,
                ElectronicsItem.product_id == product_id,
            )
            .order_by(ElectronicsItem.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def mark_sold(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
        order_id: UUID,
    ) -> ElectronicsItem:
        item = await self._session.get(ElectronicsItem, item_id)
        if item is None or item.tenant_id != tenant_id:
            raise NotFoundError("Electronics item not found.")
        if item.sold_order_id is not None:
            raise ConflictError("Item is already marked sold.")
        now = datetime.now(timezone.utc)
        item.sold_order_id = order_id
        item.sold_at = now
        # If the store didn't set a purchase date at receiving, fall back to
        # the sale date so warranty math still works.
        if item.purchased_on is None:
            item.purchased_on = now.date()
        await self._session.flush()
        return item

    async def mark_sold_for_line(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        order_id: UUID,
        item_id: UUID | None = None,
        serial_no: str | None = None,
        imei: str | None = None,
    ) -> ElectronicsItem | None:
        """Mark inventory sold from checkout. Prefer ``item_id``; otherwise resolve
        a single open unit by ``serial_no`` or ``imei`` for ``product_id``.
        """
        if item_id is not None:
            return await self.mark_sold(
                tenant_id=tenant_id, item_id=item_id, order_id=order_id
            )
        item: ElectronicsItem | None = None
        if serial_no and serial_no.strip():
            item = await self.lookup_by_serial(tenant_id=tenant_id, serial_no=serial_no.strip())
        if item is None and imei and imei.strip():
            item = await self.lookup_by_imei(tenant_id=tenant_id, imei=imei.strip())
        if item is None or item.product_id != product_id:
            raise NotFoundError("No in-stock unit matches that serial/IMEI for this product.")
        if item.sold_order_id is not None:
            raise ConflictError("That unit is already sold.")
        return await self.mark_sold(
            tenant_id=tenant_id, item_id=item.id, order_id=order_id
        )

    async def check_warranty_status(
        self, *, tenant_id: UUID, serial_no: str
    ) -> tuple[ElectronicsItem, int, date | None]:
        """Return (item, days_remaining, expiry_date) for the given serial.

        ``days_remaining`` is negative when the warranty has lapsed. When the
        unit has no warranty months or no purchase date, we report 0 / None
        so the caller displays "not covered" instead of an error.
        """
        item = await self.lookup_by_serial(tenant_id=tenant_id, serial_no=serial_no)
        if item is None:
            raise NotFoundError("No item with that serial number.")
        expires = _warranty_expiry(item.purchased_on, item.warranty_months)
        if expires is None:
            return item, 0, None
        today = datetime.now(timezone.utc).date()
        return item, _days_between(today, expires), expires
