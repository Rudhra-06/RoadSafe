from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.utils.enums import InvoiceStatus, PaymentStatus


class PartUsageCreate(BaseModel):
    part_id: str
    quantity: int = Field(..., ge=1, le=100)


class JobCompletionCreate(BaseModel):
    service_id: str
    parts: List[PartUsageCreate] = []
    notes: Optional[str] = Field(None, max_length=2000)


class InvoiceLineRead(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    line_type: str
    class Config: from_attributes = True


class InvoiceRead(BaseModel):
    id: str
    invoice_number: str
    ticket_id: str
    customer_id: str
    service_total: Decimal
    parts_total: Decimal
    fees_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    status: InvoiceStatus
    created_at: datetime
    lines: List[InvoiceLineRead] = []
    class Config: from_attributes = True


class RazorpayOrderRead(BaseModel):
    invoice_id: str
    order_id: str
    amount: int
    currency: str
    key_id: str


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentRead(BaseModel):
    id: str
    invoice_id: str
    provider_order_id: str
    provider_payment_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    class Config: from_attributes = True


class ReviewCreate(BaseModel):
    ticket_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewRead(BaseModel):
    id: str
    ticket_id: str
    customer_id: str
    responder_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True
