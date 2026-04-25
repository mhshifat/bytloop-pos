from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.pet_store.schemas import (
    PetProductMetadataRead,
    UpsertMetadataRequest,
)
from src.verticals.retail.pet_store.service import PetStoreService

router = APIRouter(prefix="/pet-store", tags=["pet-store"])


@router.put(
    "/metadata",
    response_model=PetProductMetadataRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_metadata(
    req: UpsertMetadataRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PetProductMetadataRead:
    row = await PetStoreService(db).upsert_metadata(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        target_species=req.target_species,
        target_breed=req.target_breed,
        life_stage=req.life_stage,
        weight_range_lbs=req.weight_range_lbs,
        is_prescription_food=req.is_prescription_food,
    )
    return PetProductMetadataRead.model_validate(row)


@router.get(
    "/by-species/{species}",
    response_model=list[PetProductMetadataRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_by_species(
    species: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PetProductMetadataRead]:
    rows = await PetStoreService(db).list_by_species(
        tenant_id=user.tenant_id, species=species
    )
    return [PetProductMetadataRead.model_validate(r) for r in rows]


@router.get(
    "/prescription-foods",
    response_model=list[PetProductMetadataRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_prescription_foods(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PetProductMetadataRead]:
    rows = await PetStoreService(db).list_prescription_foods(
        tenant_id=user.tenant_id
    )
    return [PetProductMetadataRead.model_validate(r) for r in rows]
