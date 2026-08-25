from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PartBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))
    stock_quantity: int = Field(..., ge=0)

    @field_validator("name")
    def name_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Part name cannot be empty or whitespace only.")
        return value.strip()


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("name")
    def name_must_not_be_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Part name cannot be empty or whitespace only.")
        return value.strip() if value is not None else value


class PartResponse(PartBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True