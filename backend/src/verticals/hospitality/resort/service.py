from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.hospitality.hotel.api import HotelService
from src.verticals.hospitality.resort.entity import (
    ResortPackage,
    ResortPackageBooking,
)


class ResortService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Packages
    # ──────────────────────────────────────────────

    async def list_packages(self, *, tenant_id: UUID) -> list[ResortPackage]:
        stmt = (
            select(ResortPackage)
            .where(ResortPackage.tenant_id == tenant_id)
            .order_by(ResortPackage.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_package(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        per_night_price_cents: int,
        includes_meals: bool = True,
        includes_drinks: bool = False,
        includes_spa: bool = False,
        includes_activities: bool = False,
    ) -> ResortPackage:
        existing = await self._get_package(tenant_id=tenant_id, code=code)
        if existing is not None:
            raise ConflictError("A package with that code already exists.")
        package = ResortPackage(
            tenant_id=tenant_id,
            code=code,
            name=name,
            per_night_price_cents=per_night_price_cents,
            includes_meals=includes_meals,
            includes_drinks=includes_drinks,
            includes_spa=includes_spa,
            includes_activities=includes_activities,
        )
        self._session.add(package)
        await self._session.flush()
        return package

    async def _get_package(
        self, *, tenant_id: UUID, code: str
    ) -> ResortPackage | None:
        stmt = select(ResortPackage).where(
            ResortPackage.tenant_id == tenant_id,
            ResortPackage.code == code,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # ──────────────────────────────────────────────
    # Attach to reservation
    # ──────────────────────────────────────────────

    async def attach_to_reservation(
        self,
        *,
        tenant_id: UUID,
        reservation_id: UUID,
        package_code: str,
        nights: int,
    ) -> ResortPackageBooking:
        if nights <= 0:
            raise ConflictError("Nights must be at least 1.")
        package = await self._get_package(tenant_id=tenant_id, code=package_code)
        if package is None:
            raise NotFoundError("Package not found.")

        total_cents = nights * package.per_night_price_cents

        # Post the bundled charge against the reservation's folio — this way
        # the existing hotel folio endpoint already shows the package total
        # alongside any room service / bar incidentals.
        await HotelService(self._session).post_charge(
            tenant_id=tenant_id,
            reservation_id=reservation_id,
            description=f"Resort package: {package.name} ({nights} night{'s' if nights != 1 else ''})",
            amount_cents=total_cents,
        )

        booking = ResortPackageBooking(
            tenant_id=tenant_id,
            reservation_id=reservation_id,
            package_code=package.code,
            nights=nights,
            total_package_cents=total_cents,
        )
        self._session.add(booking)
        await self._session.flush()
        return booking

    async def amenities_included(
        self, *, tenant_id: UUID, reservation_id: UUID
    ) -> tuple[ResortPackageBooking, ResortPackage]:
        """Return the (booking, package) attached to a reservation.

        Used by the bar / spa desk to check whether an amenity is already
        covered by a package before charging the guest.
        """
        stmt = (
            select(ResortPackageBooking)
            .where(
                ResortPackageBooking.tenant_id == tenant_id,
                ResortPackageBooking.reservation_id == reservation_id,
            )
            .order_by(ResortPackageBooking.attached_at.desc())
        )
        booking = (await self._session.execute(stmt)).scalars().first()
        if booking is None:
            raise NotFoundError("No package attached to that reservation.")
        package = await self._get_package(
            tenant_id=tenant_id, code=booking.package_code
        )
        if package is None:
            # Package was deleted after attachment — treat as not-found for
            # the UI; the folio charge still stands.
            raise NotFoundError("Attached package is no longer defined.")
        return booking, package
