from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import TicketStatus


class TicketStatusLog(BaseModel):
    __tablename__ = "ticket_status_log"

    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(SQLEnum(TicketStatus), nullable=True)
    new_status = Column(SQLEnum(TicketStatus), nullable=False)
    changed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="status_logs")