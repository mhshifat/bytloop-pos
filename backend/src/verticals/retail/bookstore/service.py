from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, ValidationError
from src.modules.catalog.api import Product


def _strip(isbn: str) -> str:
    """Remove dashes, spaces, and other decorations. The check character may
    be ``X`` (ISBN-10) or a digit."""
    return "".join(ch for ch in isbn if ch.isalnum()).upper()


def _isbn10_check(digits9: str) -> str:
    """Compute the check char for a 9-digit ISBN-10 core. Returns '0'..'9' or 'X'."""
    total = sum((i + 1) * int(d) for i, d in enumerate(digits9))
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def _isbn13_check(digits12: str) -> str:
    """EAN-13 check digit: alternating weights 1/3, tens complement of the sum."""
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits12))
    return str((10 - total % 10) % 10)


def _normalize_candidates(isbn: str) -> list[str]:
    """Return the set of ISBN strings we should try against ``Product.barcode``.

    Given an ISBN-10 we produce its ISBN-13 twin (prefix ``978`` + new check
    digit) and vice versa. We always include the stripped input itself because
    that's what the shop is most likely to have typed into the barcode field.
    The check digit we receive is trusted as-is — we're not here to validate
    catalog data, just to match what might be stored.
    """
    stripped = _strip(isbn)
    if not stripped:
        raise ValidationError("ISBN cannot be empty.")

    candidates: list[str] = [stripped]

    if len(stripped) == 10 and stripped[:9].isdigit():
        core = stripped[:9]
        candidates.append("978" + core + _isbn13_check("978" + core))
    elif len(stripped) == 13 and stripped.isdigit() and stripped.startswith(("978", "979")):
        # ISBN-10 only exists for the 978- prefix. 979- books have no 10-digit form.
        if stripped.startswith("978"):
            core = stripped[3:12]
            candidates.append(core + _isbn10_check(core))
    else:
        raise ValidationError(
            "ISBN must be 10 or 13 characters (dashes and spaces are allowed)."
        )

    # Preserve order, dedupe — some inputs are already both forms (rare but
    # cheap to guard against).
    seen: set[str] = set()
    ordered: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


class BookstoreService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_isbn(self, *, tenant_id: UUID, isbn: str) -> Product:
        candidates = _normalize_candidates(isbn)
        # One query with IN(...) rather than N probes — the list is at most
        # two entries, but the single round-trip is cleaner and lets Postgres
        # pick the ``ix_products_barcode`` index either way.
        stmt = select(Product).where(
            Product.tenant_id == tenant_id,
            Product.barcode.in_(candidates),
        )
        product = (await self._session.execute(stmt)).scalars().first()
        if product is None:
            raise NotFoundError("No book found for that ISBN.")
        return product
