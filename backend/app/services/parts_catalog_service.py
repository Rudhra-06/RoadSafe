from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.parts_catalog import Part
from app.schemas.parts_catalog import PartCreate, PartUpdate


class PartsCatalogService:

    @staticmethod
    async def create_part(db: AsyncSession, payload: PartCreate) -> Part:
        if payload.part_number:
            existing = await db.execute(select(Part).filter(Part.part_number == payload.part_number))
            if existing.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Part number '{payload.part_number}' already exists."
                )

        part = Part(
            name=payload.name,
            part_number=payload.part_number,
            description=payload.description,
            unit_price=payload.unit_price,
            stock_quantity=payload.stock_quantity,
            is_active=True
        )
        db.add(part)
        await db.commit()
        await db.refresh(part)
        return part

    @staticmethod
    async def get_part(db: AsyncSession, part_id: str) -> Part:
        result = await db.execute(select(Part).filter(Part.id == part_id))
        part = result.scalars().first()
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Part with ID '{part_id}' not found."
            )
        return part

    @staticmethod
    async def list_parts(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True
    ) -> List[Part]:
        query = select(Part)
        if active_only:
            query = query.filter(Part.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_part(db: AsyncSession, part_id: str, payload: PartUpdate) -> Part:
        part = await PartsCatalogService.get_part(db, part_id)
        
        if payload.part_number and payload.part_number != part.part_number:
            existing = await db.execute(select(Part).filter(Part.part_number == payload.part_number))
            if existing.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Part number '{payload.part_number}' already exists."
                )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(part, key, value)
        await db.commit()
        await db.refresh(part)
        return part

    @staticmethod
    async def deactivate_part(db: AsyncSession, part_id: str) -> Part:
        part = await PartsCatalogService.get_part(db, part_id)
        part.is_active = False
        await db.commit()
        await db.refresh(part)
        return part