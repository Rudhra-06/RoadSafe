from sqlalchemy import Column, String, Text, Numeric, Boolean
from app.db.base import BaseModel


class Service(BaseModel):
    __tablename__ = "services"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)