from pydantic import BaseModel, EmailStr, Field
from app.utils.enums import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2)
    phone_number: str = Field(..., min_length=5)
    role: UserRole = UserRole.CUSTOMER


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserAuthResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone_number: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthResponse