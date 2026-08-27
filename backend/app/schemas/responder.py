from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.utils.enums import ResponderType


class SkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=2)


class SkillRead(BaseModel):
    id: str
    responder_id: str
    skill_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResponderLocationCreate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class ResponderLocationRead(BaseModel):
    id: str
    responder_id: str
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True


class ResponderAvailabilityUpdate(BaseModel):
    is_available: Optional[bool] = None
    is_online: Optional[bool] = None


class ResponderCreate(BaseModel):
    type: ResponderType
    skills: List[str] = []


class ResponderRead(BaseModel):
    id: str
    user_id: str
    type: ResponderType
    is_available: bool
    is_online: bool
    shop_name: Optional[str] = None
    shop_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    skills: List[SkillRead] = []
    latest_location: Optional[ResponderLocationRead] = None

    class Config:
        from_attributes = True


class ResponderNearbyRead(BaseModel):
    responder_id: str
    user_id: str
    type: ResponderType
    latitude: float
    longitude: float
    distance_km: float
    is_available: bool
    full_name: str
    shop_name: Optional[str] = None
    shop_address: Optional[str] = None
    skills: List[str] = []


class ResponderPublicRead(ResponderNearbyRead):
    phone_number: Optional[str] = None
