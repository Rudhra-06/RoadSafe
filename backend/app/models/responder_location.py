from sqlalchemy import Column, Float, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class ResponderLocation(BaseModel):
    __tablename__ = "responder_locations"

    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Relationships
    responder = relationship("Responder", back_populates="locations")

    __table_args__ = (
        Index("idx_responder_loc_coords", "latitude", "longitude"),
    )