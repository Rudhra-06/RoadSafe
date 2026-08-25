from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import AssignmentStatus


class TicketAssignment(BaseModel):
    __tablename__ = "ticket_assignments"

    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(AssignmentStatus), nullable=False, default=AssignmentStatus.OFFERED)
    score = Column(Float, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="assignments")
    responder = relationship("Responder", back_populates="assignments")