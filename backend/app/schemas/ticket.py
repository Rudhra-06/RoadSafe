from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.enums import TicketStatus, TicketPriority, ResponderType, AssignmentStatus


class TicketCreate(BaseModel):
    vehicle_type: str = Field(..., min_length=2)
    service_type: ResponderType
    description: str = Field(..., min_length=5)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    priority: TicketPriority = TicketPriority.MEDIUM
    contact_phone: Optional[str] = None

    @field_validator("service_type", mode="before")
    @classmethod
    def map_legacy_service_types(cls, value):
        # Compatibility for existing clients that used the original label.
        return {"TOW_TRUCK": "TOWING_OPERATOR"}.get(value, value)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    reason: Optional[str] = None


class TicketAssignRequest(BaseModel):
    responder_id: str


class AssignmentDecision(BaseModel):
    accepted: bool


class StatusLogRead(BaseModel):
    id: str
    ticket_id: str
    previous_status: Optional[TicketStatus] = None
    new_status: TicketStatus
    changed_by_user_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentRead(BaseModel):
    id: str
    ticket_id: str
    responder_id: str
    status: AssignmentStatus
    score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketRead(BaseModel):
    id: str
    customer_id: str
    vehicle_type: str
    service_type: ResponderType
    description: str
    latitude: float
    longitude: float
    priority: TicketPriority
    status: TicketStatus
    contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assignments: List[AssignmentRead] = []
    status_logs: List[StatusLogRead] = []

    class Config:
        from_attributes = True


class TicketCreateResponse(BaseModel):
    ticket: TicketRead
    assignment: Optional[AssignmentRead] = None
