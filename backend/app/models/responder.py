from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import ResponderType


class Responder(BaseModel):
    __tablename__ = "responders"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    type = Column(SQLEnum(ResponderType), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    is_online = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="responder_profile")
    skills = relationship("ResponderSkill", back_populates="responder", cascade="all, delete-orphan")
    locations = relationship("ResponderLocation", back_populates="responder", cascade="all, delete-orphan")
    assignments = relationship("TicketAssignment", back_populates="responder", cascade="all, delete-orphan")