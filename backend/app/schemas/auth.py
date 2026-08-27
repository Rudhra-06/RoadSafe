from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator
from app.utils.enums import UserRole, ResponderType
from typing import List, Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2)
    phone_number: Optional[str] = Field(
        default="",
        validation_alias=AliasChoices("phone_number", "phone"),
    )
    role: UserRole = UserRole.CUSTOMER
    responder_type: ResponderType = ResponderType.ROADSIDE_TECHNICIAN
    skills: List[str] = Field(default_factory=list)
    shop_name: Optional[str] = Field(None, max_length=255)
    shop_address: Optional[str] = None

    @field_validator("phone_number", mode="before")
    @classmethod
    def sanitize_phone(cls, v):
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("skills", mode="before")
    @classmethod
    def sanitize_skills(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(s).strip() for s in v if s]
        return [str(v).strip()]



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
