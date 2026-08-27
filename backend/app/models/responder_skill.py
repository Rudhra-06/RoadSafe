import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class ResponderSkill(Base):
    __tablename__ = "responder_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    responder = relationship("Responder", back_populates="skills")