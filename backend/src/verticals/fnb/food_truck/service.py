from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.fnb.food_truck.entity import (
    DailyMenu,
    DailyMenuItem,
    TruckLocation,
)
from src.verticals.fnb.food_truck.schemas import DailyMenuItemInput


class FoodTruckService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Locations
    # ──────────────────────────────────────────────

    async def set_location(
        self,
        *,
        tenant_id: UUID,
        location_name: str,
        latitude: Decimal,
        longitude: Decimal,
        starts_at: datetime,
        ends_at: datetime,
        notes: str | None = None,
    ) -> TruckLocation:
        if ends_at <= starts_at:
            raise ValidationError("ends_at must be after starts_at.")
        location = TruckLocation(
            tenant_id=tenant_id,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            starts_at=starts_at,
            ends_at=ends_at,
            notes=notes,
        )
        self._session.add(location)
        await self._session.flush()
        return location

    async def current_location(self, *, tenant_id: UUID) -> TruckLocation | None:
        """The active location (now between starts_at and ends_at).

        If schedules overlap we return the most recently created one —
        the dispatcher's latest override wins.
        """
        now = datetime.now(tz=UTC)
        stmt = (
            select(TruckLocation)
            .where(
                TruckLocation.tenant_id == tenant_id,
                TruckLocation.starts_at <= now,
                TruckLocation.ends_at >= now,
            )
            .order_by(TruckLocation.created_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_locations(
        self, *, tenant_id: UUID, upcoming_only: bool = False
    ) -> list[TruckLocation]:
        stmt = select(TruckLocation).where(TruckLocation.tenant_id == tenant_id)
        if upcoming_only:
            stmt = stmt.where(TruckLocation.ends_at >= datetime.now(tz=UTC))
        stmt = stmt.order_by(TruckLocation.starts_at)
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Daily menus
    # ──────────────────────────────────────────────

    async def publish_menu(
        self,
        *,
        tenant_id: UUID,
        menu_date: date,
        items: list[DailyMenuItemInput],
        notes: str | None = None,
    ) -> DailyMenu:
        if not items:
            raise ValidationError("At least one menu item is required.")

        # Dedupe input — same product cannot appear twice on the same menu.
        seen: set[UUID] = set()
        for item in items:
            if item.product_id in seen:
                raise ValidationError(
                    "Each product may appear only once on a daily menu."
                )
            seen.add(item.product_id)

        # Replace any existing menu for this date (republish).
        stmt = select(DailyMenu).where(
            DailyMenu.tenant_id == tenant_id,
            DailyMenu.menu_date == menu_date,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

        menu = DailyMenu(
            tenant_id=tenant_id,
            menu_date=menu_date,
            notes=notes,
        )
        self._session.add(menu)
        await self._session.flush()

        self._session.add_all(
            [
                DailyMenuItem(
                    tenant_id=tenant_id,
                    menu_id=menu.id,
                    product_id=i.product_id,
                    daily_price_cents_override=i.daily_price_cents_override,
                    sold_out=i.sold_out,
                    sort_order=i.sort_order,
                )
                for i in items
            ]
        )
        await self._session.flush()
        return menu

    async def _get_menu_for_date(
        self, *, tenant_id: UUID, menu_date: date
    ) -> DailyMenu | None:
        stmt = select(DailyMenu).where(
            DailyMenu.tenant_id == tenant_id,
            DailyMenu.menu_date == menu_date,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def today_menu(
        self, *, tenant_id: UUID
    ) -> tuple[DailyMenu, list[DailyMenuItem]]:
        today = datetime.now(tz=UTC).date()
        menu = await self._get_menu_for_date(tenant_id=tenant_id, menu_date=today)
        if menu is None:
            raise NotFoundError("No menu published for today.")
        items = await self.list_menu_items(tenant_id=tenant_id, menu_id=menu.id)
        return menu, items

    async def list_menu_items(
        self, *, tenant_id: UUID, menu_id: UUID
    ) -> list[DailyMenuItem]:
        stmt = (
            select(DailyMenuItem)
            .where(
                DailyMenuItem.tenant_id == tenant_id,
                DailyMenuItem.menu_id == menu_id,
            )
            .order_by(DailyMenuItem.sort_order, DailyMenuItem.id)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def mark_sold_out(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
        sold_out: bool,
    ) -> DailyMenuItem:
        item = await self._session.get(DailyMenuItem, item_id)
        if item is None or item.tenant_id != tenant_id:
            raise NotFoundError("Menu item not found.")
        if item.sold_out == sold_out:
            raise ConflictError("Menu item is already in that state.")
        item.sold_out = sold_out
        await self._session.flush()
        return item
