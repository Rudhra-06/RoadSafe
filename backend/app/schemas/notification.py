from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    ticket_id: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: bool = True
