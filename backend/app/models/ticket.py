from sqlalchemy import Column, String, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import TicketStatus, TicketPriority, ResponderType


class Ticket(BaseModel):
    __tablename__ = "tickets"

    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_type = Column(String(100), nullable=False)
    service_type = Column(SQLEnum(ResponderType), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority = Column(SQLEnum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus), nullable=False, default=TicketStatus.REQUESTED, index=True)
    contact_phone = Column(String(50), nullable=True)

    # Relationships
    customer = relationship("User", back_populates="customer_tickets")
    assignments = relationship("TicketAssignment", back_populates="ticket", cascade="all, delete-orphan")
    status_logs = relationship("TicketStatusLog", back_populates="ticket", cascade="all, delete-orphan")