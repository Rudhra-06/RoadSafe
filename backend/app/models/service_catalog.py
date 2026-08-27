from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer
from app.db.base import BaseModel


class Service(BaseModel):
    __tablename__ = "services"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    estimated_duration_minutes = Column(Integer, nullable=True)
    features = Column(Text, nullable=True)
    included_items = Column(Text, nullable=True)
    possible_parts = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
