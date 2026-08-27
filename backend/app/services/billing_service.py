import asyncio
import base64
import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import Request, urlopen
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.billing import Invoice, InvoiceLine, InvoiceStatus, Payment, PaymentStatus
from app.models.parts_catalog import Part
from app.models.service_catalog import Service
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.responder import Responder
from app.utils.enums import AssignmentStatus, TicketStatus


class BillingService:
    @staticmethod
    async def create_invoice_for_completion(db: AsyncSession, ticket_id: str, responder_user_id: str, payload):
        ticket = (await db.execute(select(Ticket).options(selectinload(Ticket.assignments)).where(Ticket.id == ticket_id))).scalars().first()
        if not ticket: raise HTTPException(404, "Ticket not found")
        if ticket.status != TicketStatus.IN_SERVICE: raise HTTPException(400, "A job must be in service before it can be completed")
        responder = (await db.execute(select(Responder).where(Responder.user_id == responder_user_id))).scalars().first()
        valid = responder is not None and any(a.status == AssignmentStatus.ACCEPTED and a.responder_id == responder.id for a in ticket.assignments)
        if not valid: raise HTTPException(403, "Only the assigned responder can complete this job")
        existing = (await db.execute(select(Invoice).where(Invoice.ticket_id == ticket_id))).scalars().first()
        if existing: raise HTTPException(409, "An invoice already exists for this ticket")
        service = (await db.execute(select(Service).where(Service.id == payload.service_id, Service.is_active == True))).scalars().first()
        if not service: raise HTTPException(404, "Active service not found")
        service_total = Decimal(service.base_price)
        lines = [InvoiceLine(description=service.name, quantity=1, unit_price=service_total, line_total=service_total, line_type="SERVICE")]
        parts_total = Decimal("0.00")
        for usage in payload.parts:
            part = (await db.execute(select(Part).where(Part.id == usage.part_id, Part.is_active == True).with_for_update())).scalars().first()
            if not part: raise HTTPException(404, "Part not found")
            if part.stock_quantity < usage.quantity: raise HTTPException(400, f"Insufficient stock for {part.name}")
            line_total = (Decimal(part.unit_price) * usage.quantity).quantize(Decimal("0.01"))
            part.stock_quantity -= usage.quantity
            parts_total += line_total
            lines.append(InvoiceLine(part_id=part.id, description=part.name, quantity=usage.quantity, unit_price=part.unit_price, line_total=line_total, line_type="PART"))
        subtotal = service_total + parts_total
        tax = (subtotal * Decimal(str(settings.INVOICE_TAX_RATE)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        invoice = Invoice(invoice_number=f"RS-{datetime.utcnow():%Y%m%d}-{ticket.id[:8].upper()}", ticket_id=ticket.id, customer_id=ticket.customer_id, service_total=service_total, parts_total=parts_total, fees_total=Decimal("0.00"), tax_total=tax, grand_total=subtotal + tax, status=InvoiceStatus.PENDING)
        invoice.lines = lines
        db.add(invoice)
        ticket.status = TicketStatus.COMPLETED
        await db.commit()
        return await BillingService.get_invoice(db, invoice.id)

    @staticmethod
    async def get_invoice(db, invoice_id):
        invoice = (await db.execute(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))).scalars().first()
        if not invoice: raise HTTPException(404, "Invoice not found")
        return invoice

    @staticmethod
    async def list_invoices(db, customer_id=None):
        q = select(Invoice).options(selectinload(Invoice.lines)).order_by(Invoice.created_at.desc())
        if customer_id: q = q.where(Invoice.customer_id == customer_id)
        return (await db.execute(q)).scalars().all()

    @staticmethod
    async def _razorpay_create_order(amount_paise, receipt):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET: raise HTTPException(503, "Payments are not configured")
        data = json.dumps({"amount": amount_paise, "currency": settings.RAZORPAY_CURRENCY, "receipt": receipt}).encode()
        auth = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
        def request():
            req = Request("https://api.razorpay.com/v1/orders", data=data, headers={"Content-Type":"application/json", "Authorization":f"Basic {auth}"}, method="POST")
            return json.loads(urlopen(req, timeout=15).read())
        try: return await asyncio.to_thread(request)
        except Exception: raise HTTPException(502, "Unable to create payment order. Please try again.")

    @staticmethod
    async def create_payment_order(db, invoice):
        if invoice.status == InvoiceStatus.PAID: raise HTTPException(409, "Invoice is already paid")
        existing = (await db.execute(select(Payment).where(Payment.invoice_id == invoice.id, Payment.status == PaymentStatus.CREATED))).scalars().first()
        if existing: return existing
        amount = int((Decimal(invoice.grand_total) * 100).quantize(Decimal("1")))
        remote = await BillingService._razorpay_create_order(amount, invoice.invoice_number)
        payment = Payment(invoice_id=invoice.id, provider_order_id=remote["id"], amount=invoice.grand_total, currency=remote.get("currency", settings.RAZORPAY_CURRENCY), status=PaymentStatus.CREATED)
        db.add(payment); await db.commit(); await db.refresh(payment); return payment

    @staticmethod
    async def verify_payment(db, invoice, payload):
        payment = (await db.execute(select(Payment).where(Payment.provider_order_id == payload.razorpay_order_id))).scalars().first()
        if not payment or payment.invoice_id != invoice.id: raise HTTPException(400, "Invalid payment order")
        if invoice.status == InvoiceStatus.PAID or payment.status == PaymentStatus.VERIFIED: raise HTTPException(409, "Invoice is already paid")
        expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(), hashlib.sha256).hexdigest() if settings.RAZORPAY_KEY_SECRET else ""
        if not hmac.compare_digest(expected, payload.razorpay_signature):
            payment.status = PaymentStatus.FAILED; await db.commit(); raise HTTPException(400, "Payment signature could not be verified")
        payment.provider_payment_id = payload.razorpay_payment_id; payment.status = PaymentStatus.VERIFIED; invoice.status = InvoiceStatus.PAID
        await db.commit(); return payment
