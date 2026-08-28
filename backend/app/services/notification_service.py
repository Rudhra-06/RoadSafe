from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from app.websocket.manager import ws_manager


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        title: str,
        message: str,
        type: str = "SYSTEM",
        ticket_id: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            ticket_id=ticket_id,
            is_read=False
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

        # Real-time WebSocket push to ticket subscribers
        if ticket_id:
            await ws_manager.broadcast_to_ticket(
                ticket_id=ticket_id,
                message={
                    "event": "NOTIFICATION",
                    "id": notif.id,
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "type": type,
                    "ticket_id": ticket_id,
                    "created_at": notif.created_at.isoformat()
                }
            )

        return notif

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        user_id: str,
        limit: int = 50
    ) -> List[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_id: str,
        user_id: str
    ) -> Optional[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        notif = result.scalars().first()
        if not notif:
            return None
        notif.is_read = True
        await db.commit()
        await db.refresh(notif)
        return notif
