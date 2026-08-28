from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="SYSTEM")  # DISPATCH, STATUS, BILLING, SYSTEM
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    is_read = Column(Boolean, nullable=False, default=False)

    user = relationship("User")
    ticket = relationship("Ticket")
