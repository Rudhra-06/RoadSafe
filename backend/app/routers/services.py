from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.dependencies import RoleChecker
from app.schemas.service_catalog import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.service_catalog_service import ServiceCatalogService
from app.utils.enums import UserRole


router = APIRouter(prefix="/services", tags=["Billable Services"])


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
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_or_manager)]
)
async def create_service(
    payload: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new billable service (Admin/Manager only)."""
    return await ServiceCatalogService.create_service(db, payload)


@router.get(
    "",
    response_model=List[ServiceResponse],
    dependencies=[Depends(authenticated_users)]
)
async def list_services(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List billable services."""
    return await ServiceCatalogService.list_services(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(authenticated_users)]
)
async def get_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get billable service details by ID."""
    return await ServiceCatalogService.get_service(db, service_id)


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(admin_or_manager)]
)
async def update_service(
    service_id: str,
    payload: ServiceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a billable service (Admin/Manager only)."""
    return await ServiceCatalogService.update_service(
        db,
        service_id,
        payload
    )


@router.delete(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(admin_or_manager)]
)
async def deactivate_service(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete/deactivate a service (Admin/Manager only)."""
    return await ServiceCatalogService.deactivate_service(
        db,
        service_id
    )