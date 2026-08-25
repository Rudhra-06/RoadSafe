from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.core.dependencies import RoleChecker
from app.models.user import User
from app.schemas.user import UserRead
from app.utils.enums import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

admin_or_manager = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])


@router.get("", response_model=List[UserRead], dependencies=[Depends(admin_or_manager)])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List registered users (Admin/Manager only).
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(admin_or_manager)])
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile by User ID (Admin/Manager only).
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user