from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.dependencies import RoleChecker
from app.schemas.parts_catalog import PartCreate, PartUpdate, PartResponse
from app.services.parts_catalog_service import PartsCatalogService
from app.utils.enums import UserRole


router = APIRouter(prefix="/parts", tags=["Parts Inventory"])


admin_or_manager = RoleChecker([
    UserRole.ADMIN,
    UserRole.MANAGER
])


authenticated_users = RoleChecker([
    UserRole.ADMIN,
    UserRole.MANAGER,
    UserRole.RESPONDER,
    UserRole.CUSTOMER
])


@router.post(
    "",
    response_model=PartResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_or_manager)]
)
async def create_part(
    payload: PartCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new part item (Admin/Manager only)."""
    return await PartsCatalogService.create_part(db, payload)


@router.get(
    "",
    response_model=List[PartResponse],
    dependencies=[Depends(authenticated_users)]
)
async def list_parts(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List parts inventory."""
    return await PartsCatalogService.list_parts(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get(
    "/{part_id}",
    response_model=PartResponse,
    dependencies=[Depends(authenticated_users)]
)
async def get_part(
    part_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get part details by ID."""
    return await PartsCatalogService.get_part(db, part_id)


@router.patch(
    "/{part_id}",
    response_model=PartResponse,
    dependencies=[Depends(admin_or_manager)]
)
async def update_part(
    part_id: str,
    payload: PartUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update part item details (Admin/Manager only)."""
    return await PartsCatalogService.update_part(
        db,
        part_id,
        payload
    )


@router.delete(
    "/{part_id}",
    response_model=PartResponse,
    dependencies=[Depends(admin_or_manager)]
)
async def deactivate_part(
    part_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete/deactivate a part item (Admin/Manager only)."""
    return await PartsCatalogService.deactivate_part(db, part_id)