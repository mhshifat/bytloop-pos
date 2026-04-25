from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.modules.sales.api import OrderType, PaymentMethod, SalesService
from src.modules.sales.schemas import CartItemInput
from src.verticals.services.gas_station.entity import (
    DispenserReading,
    DispenserStatus,
    FuelDispenser,
    FuelType,
)


class GasStationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Dispensers
    # ──────────────────────────────────────────────

    async def list_dispensers(self, *, tenant_id: UUID) -> list[FuelDispenser]:
        stmt = (
            select(FuelDispenser)
            .where(FuelDispenser.tenant_id == tenant_id)
            .order_by(FuelDispenser.label)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_dispenser(
        self,
        *,
        tenant_id: UUID,
        label: str,
        fuel_type: FuelType,
        price_per_liter_cents: int,
        product_id: UUID | None = None,
    ) -> FuelDispenser:
        dispenser = FuelDispenser(
            tenant_id=tenant_id,
            label=label,
            fuel_type=fuel_type,
            price_per_liter_cents=price_per_liter_cents,
            product_id=product_id,
            status=DispenserStatus.ACTIVE,
        )
        self._session.add(dispenser)
        await self._session.flush()
        return dispenser

    async def _last_reading(
        self, *, tenant_id: UUID, dispenser_id: UUID
    ) -> DispenserReading | None:
        stmt = (
            select(DispenserReading)
            .where(
                DispenserReading.tenant_id == tenant_id,
                DispenserReading.dispenser_id == dispenser_id,
            )
            .order_by(DispenserReading.taken_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # ──────────────────────────────────────────────
    # Readings + sale
    # ──────────────────────────────────────────────

    async def record_reading(
        self,
        *,
        tenant_id: UUID,
        cashier_id: UUID,
        dispenser_id: UUID,
        totalizer_reading: float,
    ) -> DispenserReading:
        dispenser = await self._session.get(FuelDispenser, dispenser_id)
        if dispenser is None or dispenser.tenant_id != tenant_id:
            raise NotFoundError("Dispenser not found.")
        if dispenser.status != DispenserStatus.ACTIVE:
            raise ConflictError("Dispenser is not active.")
        if dispenser.product_id is None:
            raise ValidationError(
                "Dispenser is missing a linked catalog product; cannot bill fuel."
            )

        prev = await self._last_reading(tenant_id=tenant_id, dispenser_id=dispenser_id)
        prev_total = float(prev.totalizer_reading) if prev is not None else 0.0
        delta = float(totalizer_reading) - prev_total
        if delta < 0:
            raise ValidationError(
                "Totalizer reading is lower than the previous reading."
            )

        # Round litres up to the nearest whole for billing — keep the decimal
        # delta on the audit record. Fractional fuel volumes are cosmetic at
        # the pump; commercial practice is integer litres per transaction.
        billable_liters = int(round(delta))

        order_id: UUID | None = None
        if billable_liters > 0:
            sale = await SalesService(self._session).checkout(
                tenant_id=tenant_id,
                cashier_id=cashier_id,
                items=[
                    CartItemInput(
                        product_id=dispenser.product_id,
                        quantity=billable_liters,
                    )
                ],
                order_type=OrderType.RETAIL,
                payment_method=PaymentMethod.CASH,
                amount_tendered_cents=None,
            )
            order_id = sale.order.id

        reading = DispenserReading(
            tenant_id=tenant_id,
            dispenser_id=dispenser_id,
            totalizer_reading=totalizer_reading,
            liters_dispensed=delta,
            order_id=order_id,
        )
        self._session.add(reading)
        await self._session.flush()
        return reading

    async def list_readings(
        self, *, tenant_id: UUID, dispenser_id: UUID
    ) -> list[DispenserReading]:
        stmt = (
            select(DispenserReading)
            .where(
                DispenserReading.tenant_id == tenant_id,
                DispenserReading.dispenser_id == dispenser_id,
            )
            .order_by(DispenserReading.taken_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
