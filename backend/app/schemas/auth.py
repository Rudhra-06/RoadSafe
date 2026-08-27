from pydantic import AliasChoices, BaseModel, EmailStr, Field
from app.utils.enums import UserRole, ResponderType
from typing import List, Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2)
    phone_number: str = Field(
        "",
        validation_alias=AliasChoices("phone_number", "phone"),
        min_length=0,
    )
    role: UserRole = UserRole.CUSTOMER
    responder_type: ResponderType = ResponderType.ROADSIDE_TECHNICIAN
    skills: List[str] = []
    shop_name: Optional[str] = Field(None, max_length=255)
    shop_address: Optional[str] = None


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
