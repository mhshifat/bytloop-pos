from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.bookstore.schemas import BookLookupResult
from src.verticals.retail.bookstore.service import BookstoreService

router = APIRouter(prefix="/bookstore", tags=["bookstore"])


@router.get(
    "/lookup/{isbn}",
    response_model=BookLookupResult,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def lookup_isbn(
    isbn: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BookLookupResult:
    """Resolve an ISBN-10 or ISBN-13 to the matching catalog product.

    Dashes and spaces are stripped; both ISBN forms are tried so the same
    book found either way returns the same row.
    """
    product = await BookstoreService(db).find_by_isbn(
        tenant_id=user.tenant_id, isbn=isbn
    )
    return BookLookupResult(
        id=product.id,
        name=product.name,
        sku=product.sku,
        price_cents=product.price_cents,
        currency=product.currency,
    )
