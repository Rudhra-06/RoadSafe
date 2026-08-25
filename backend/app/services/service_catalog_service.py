from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.service_catalog import Service
from app.schemas.service_catalog import ServiceCreate, ServiceUpdate


class ServiceCatalogService:

    @staticmethod
    async def create_service(db: AsyncSession, payload: ServiceCreate) -> Service:
        service = Service(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            base_price=payload.base_price,
            is_active=True
        )
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

    @staticmethod
    async def get_service(db: AsyncSession, service_id: str) -> Service:
        result = await db.execute(select(Service).filter(Service.id == service_id))
        service = result.scalars().first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service with ID '{service_id}' not found."
            )
        return service

    @staticmethod
    async def list_services(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True
    ) -> List[Service]:
        query = select(Service)
        if active_only:
            query = query.filter(Service.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_service(db: AsyncSession, service_id: str, payload: ServiceUpdate) -> Service:
        service = await ServiceCatalogService.get_service(db, service_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)
        await db.commit()
        await db.refresh(service)
        return service

    @staticmethod
    async def deactivate_service(db: AsyncSession, service_id: str) -> Service:
        service = await ServiceCatalogService.get_service(db, service_id)
        service.is_active = False
        await db.commit()
        await db.refresh(service)
        return service