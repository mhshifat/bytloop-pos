from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.modules.audit.api import AuditService
from src.modules.customers.entity import Customer
from src.modules.customers.repository import CustomerRepository
from src.modules.customers.schemas import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, session: AsyncSession, repo: CustomerRepository | None = None) -> None:
        self._session = session
        self._repo = repo or CustomerRepository(session)
        self._audit = AuditService(session)

    async def list(
        self, *, tenant_id: UUID, search: str | None, page: int, page_size: int
    ) -> tuple[list[Customer], bool]:
        offset = max(0, (page - 1) * page_size)
        return await self._repo.list(
            tenant_id=tenant_id, search=search, limit=page_size, offset=offset
        )

    async def get(self, *, tenant_id: UUID, customer_id: UUID) -> Customer:
        customer = await self._repo.get(tenant_id=tenant_id, customer_id=customer_id)
        if customer is None:
            raise NotFoundError("We couldn't find that customer.")
        return customer

    async def create(
        self, *, tenant_id: UUID, actor_id: UUID | None, data: CustomerCreate
    ) -> Customer:
        customer = await self._repo.add(
            Customer(
                tenant_id=tenant_id,
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email.lower() if data.email else None,
                phone=data.phone,
                notes=data.notes,
            )
        )
        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="customer.created",
            resource_type="customer",
            resource_id=str(customer.id),
            after={"email": customer.email, "phone": customer.phone},
        )

        from src.core.events import canonical_payload, emit

        await emit(
            "customer.created",
            canonical_payload(
                tenant_id=tenant_id,
                actor_id=actor_id,
                resource_id=str(customer.id),
                extra={"email": customer.email, "phone": customer.phone},
            ),
        )
        return customer

    async def update(
        self, *, tenant_id: UUID, customer_id: UUID, data: CustomerUpdate
    ) -> Customer:
        customer = await self.get(tenant_id=tenant_id, customer_id=customer_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        await self._session.flush()
        return customer

    async def delete(self, *, tenant_id: UUID, customer_id: UUID) -> None:
        customer = await self.get(tenant_id=tenant_id, customer_id=customer_id)
        await self._repo.delete(customer)
