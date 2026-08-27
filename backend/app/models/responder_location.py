import uuid
from datetime import datetime
from sqlalchemy import Column, Float, String, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class ResponderLocation(Base):
    __tablename__ = "responder_locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    responder = relationship("Responder", back_populates="locations")

    __table_args__ = (
        Index("idx_responder_loc_coords", "latitude", "longitude"),
    )