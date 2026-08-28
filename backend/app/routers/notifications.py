from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_claims
from app.db.database import get_db
from app.schemas.notification import NotificationRead, NotificationUpdate
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationRead])
async def list_user_notifications(
    limit: int = 50,
    claims=Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve in-app notifications for the authenticated user."""
    return await NotificationService.list_notifications(
        db, user_id=claims["user_id"], limit=limit
    )


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: str,
    claims=Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """Mark a specific notification as read."""
    notif = await NotificationService.mark_as_read(
        db, notification_id=notification_id, user_id=claims["user_id"]
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notif
