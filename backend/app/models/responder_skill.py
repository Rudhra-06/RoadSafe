from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class ResponderSkill(BaseModel):
    __tablename__ = "responder_skills"

    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)

    # Relationships
    responder = relationship("Responder", back_populates="skills")