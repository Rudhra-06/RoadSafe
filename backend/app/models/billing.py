from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.utils.enums import InvoiceStatus, PaymentStatus


class Invoice(BaseModel):
    __tablename__ = "invoices"
    invoice_number = Column(String(40), unique=True, nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="RESTRICT"), unique=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    service_total = Column(Numeric(10, 2), nullable=False, default=0)
    parts_total = Column(Numeric(10, 2), nullable=False, default=0)
    fees_total = Column(Numeric(10, 2), nullable=False, default=0)
    tax_total = Column(Numeric(10, 2), nullable=False, default=0)
    grand_total = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING, index=True)
    ticket = relationship("Ticket")
    customer = relationship("User")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(BaseModel):
    __tablename__ = "invoice_lines"
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    part_id = Column(String(36), ForeignKey("parts.id", ondelete="RESTRICT"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    line_type = Column(String(20), nullable=False)  # SERVICE or PART
    invoice = relationship("Invoice", back_populates="lines")


class Payment(BaseModel):
    __tablename__ = "payments"
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    provider = Column(String(30), nullable=False, default="RAZORPAY")
    provider_order_id = Column(String(100), unique=True, nullable=False)
    provider_payment_id = Column(String(100), unique=True, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(8), nullable=False, default="INR")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED, index=True)
    invoice = relationship("Invoice", back_populates="payments")


class Review(BaseModel):
    __tablename__ = "reviews"
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    responder_id = Column(String(36), ForeignKey("responders.id", ondelete="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
