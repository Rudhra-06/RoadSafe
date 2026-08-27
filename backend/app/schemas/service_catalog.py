from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import json


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    base_price: Decimal = Field(..., ge=Decimal("0.00"))
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    features: List[str] = []
    included_items: List[str] = []
    possible_parts: List[str] = []

    @field_validator("name")
    def name_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Service name cannot be empty or whitespace only.")
        return value.strip()


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    base_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    features: Optional[List[str]] = None
    included_items: Optional[List[str]] = None
    possible_parts: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    def name_must_not_be_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Service name cannot be empty or whitespace only.")
        return value.strip() if value is not None else value


class ServiceResponse(ServiceBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("features", "included_items", "possible_parts", mode="before")
    @classmethod
    def decode_json_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    class Config:
        from_attributes = True
