import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.enums import ResponderType, TicketStatus, TicketPriority


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    service_type = Column(Enum(ResponderType), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.REQUESTED)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("User", back_populates="customer_tickets")
    assignments = relationship("TicketAssignment", back_populates="ticket", cascade="all, delete-orphan")
    status_logs = relationship("TicketStatusLog", back_populates="ticket", cascade="all, delete-orphan")
