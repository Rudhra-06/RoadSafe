import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.enums import TicketStatus


class TicketStatusLog(Base):
    __tablename__ = "ticket_status_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(SQLEnum(TicketStatus), nullable=True)
    new_status = Column(SQLEnum(TicketStatus), nullable=False)
    changed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="status_logs")