from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.utils.enums import UserRole


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone_number: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None