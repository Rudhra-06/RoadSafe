from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import UserRole


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    responder_profile = relationship("Responder", back_populates="user", uselist=False, cascade="all, delete-orphan")
    customer_tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")