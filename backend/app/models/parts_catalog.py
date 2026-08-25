from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean
from app.db.base import BaseModel


class Part(BaseModel):
    __tablename__ = "parts"

    name = Column(String(255), nullable=False, index=True)
    part_number = Column(String(100), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    stock_quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)