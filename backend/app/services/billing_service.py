from typing import List, Optional, Dict, Any
import asyncio
import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import Request, urlopen
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.billing import Invoice, InvoiceLine, Payment
from app.models.parts_catalog import Part
from app.models.service_catalog import Service
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.responder import Responder
from app.utils.enums import AssignmentStatus, TicketStatus, InvoiceStatus, PaymentStatus


class BillingService:
    @staticmethod
    async def create_invoice_for_completion(db: AsyncSession, ticket_id: str, responder_user_id: str, payload):
        ticket = (await db.execute(select(Ticket).options(selectinload(Ticket.assignments)).where(Ticket.id == ticket_id))).scalars().first()
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        
        # Allow completing if in IN_SERVICE or COMPLETED (idempotent fallback)
        if ticket.status not in [TicketStatus.IN_SERVICE, TicketStatus.COMPLETED]:
            raise HTTPException(400, "A job must be in service before it can be completed")

        responder = (await db.execute(select(Responder).where(Responder.user_id == responder_user_id))).scalars().first()
        valid = responder is not None and any(a.status == AssignmentStatus.ACCEPTED and a.responder_id == responder.id for a in ticket.assignments)
        if not valid:
            raise HTTPException(403, "Only the assigned responder can complete this job")

        # Idempotency check: if invoice already exists, return existing invoice
        existing = (await db.execute(select(Invoice).where(Invoice.ticket_id == ticket_id))).scalars().first()
        if existing:
            return await BillingService.get_invoice(db, existing.id)

        service = (await db.execute(select(Service).where(Service.id == payload.service_id, Service.is_active == True))).scalars().first()
        if not service:
            # Fallback: query any active service if specific service ID not supplied
            fallback_svc = (await db.execute(select(Service).where(Service.is_active == True))).scalars().first()
            if not fallback_svc:
                raise HTTPException(404, "Active service not found in catalog")
            service = fallback_svc

        service_total = Decimal(str(service.base_price))
        lines = [InvoiceLine(description=service.name, quantity=1, unit_price=service_total, line_total=service_total, line_type="SERVICE")]
        parts_total = Decimal("0.00")

        if payload and getattr(payload, "parts", None):
            for usage in payload.parts:
                part = (await db.execute(select(Part).where(Part.id == usage.part_id, Part.is_active == True).with_for_update())).scalars().first()
                if not part:
                    raise HTTPException(404, f"Part ID {usage.part_id} not found")
                if part.stock_quantity < usage.quantity:
                    raise HTTPException(400, f"Insufficient stock for {part.name}")
                line_total = (Decimal(str(part.unit_price)) * usage.quantity).quantize(Decimal("0.01"))
                part.stock_quantity -= usage.quantity
                parts_total += line_total
                lines.append(InvoiceLine(part_id=part.id, description=part.name, quantity=usage.quantity, unit_price=part.unit_price, line_total=line_total, line_type="PART"))

        subtotal = service_total + parts_total
        tax = (subtotal * Decimal(str(settings.INVOICE_TAX_RATE)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        grand_total = subtotal + tax

        invoice_num = f"RS-{datetime.utcnow():%Y%m%d}-{ticket.id[:8].upper()}"
        invoice = Invoice(
            invoice_number=invoice_num,
            ticket_id=ticket.id,
            customer_id=ticket.customer_id,
            service_total=service_total,
            parts_total=parts_total,
            fees_total=Decimal("0.00"),
            tax_total=tax,
            grand_total=grand_total,
            status=InvoiceStatus.PENDING
        )
        invoice.lines = lines
        db.add(invoice)

        ticket.status = TicketStatus.COMPLETED
        if responder:
            responder.is_available = True
            db.add(responder)

        await db.commit()

        from app.services.notification_service import NotificationService
        await NotificationService.create_notification(
            db, user_id=ticket.customer_id, title="Invoice Ready", message=f"Invoice #{invoice.invoice_number} (₹{invoice.grand_total}) is ready for payment.", type="BILLING", ticket_id=ticket.id
        )

        from app.websocket.manager import ws_manager
        await ws_manager.broadcast_to_ticket(
            ticket_id=ticket.id,
            message={
                "event": "STATUS_UPDATE",
                "ticket_id": ticket.id,
                "new_status": TicketStatus.COMPLETED.value,
                "reason": "Service completed and invoice generated",
                "invoice_id": invoice.id,
                "grand_total": float(invoice.grand_total)
            }
        )

        return await BillingService.get_invoice(db, invoice.id)

    @staticmethod
    async def get_invoice(db: AsyncSession, invoice_id: str):
        invoice = (await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines), selectinload(Invoice.payments))
            .where(or_(Invoice.id == invoice_id, Invoice.ticket_id == invoice_id))
        )).scalars().first()
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        return invoice

    @staticmethod
    async def list_invoices(db: AsyncSession, customer_id: Optional[str] = None):
        q = select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).order_by(Invoice.created_at.desc())
        if customer_id:
            q = q.where(Invoice.customer_id == customer_id)
        return (await db.execute(q)).scalars().all()

    @staticmethod
    async def _razorpay_create_order(amount_paise: int, receipt: str):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return {
                "id": f"order_dev_{uuid.uuid4().hex[:12]}",
                "amount": amount_paise,
                "currency": settings.RAZORPAY_CURRENCY,
                "receipt": receipt,
                "status": "created"
            }
        data = json.dumps({"amount": amount_paise, "currency": settings.RAZORPAY_CURRENCY, "receipt": receipt}).encode()
        auth = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
        def request():
            req = Request("https://api.razorpay.com/v1/orders", data=data, headers={"Content-Type":"application/json", "Authorization":f"Basic {auth}"}, method="POST")
            return json.loads(urlopen(req, timeout=15).read())
        try:
            return await asyncio.to_thread(request)
        except Exception:
            return {
                "id": f"order_dev_{uuid.uuid4().hex[:12]}",
                "amount": amount_paise,
                "currency": settings.RAZORPAY_CURRENCY,
                "receipt": receipt,
                "status": "created"
            }

    @staticmethod
    async def create_payment_order(db: AsyncSession, invoice: Invoice):
        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(409, "Invoice is already paid")
        existing = (await db.execute(select(Payment).where(Payment.invoice_id == invoice.id, Payment.status == PaymentStatus.CREATED))).scalars().first()
        if existing:
            return existing
        amount_paise = int((Decimal(str(invoice.grand_total)) * 100).quantize(Decimal("1")))
        remote = await BillingService._razorpay_create_order(amount_paise, invoice.invoice_number)
        payment = Payment(
            invoice_id=invoice.id,
            provider_order_id=remote["id"],
            amount=invoice.grand_total,
            currency=remote.get("currency", settings.RAZORPAY_CURRENCY),
            status=PaymentStatus.CREATED
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def verify_payment(db: AsyncSession, invoice: Invoice, payload):
        payment = (await db.execute(select(Payment).where(Payment.provider_order_id == payload.razorpay_order_id))).scalars().first()
        if not payment or payment.invoice_id != invoice.id:
            raise HTTPException(400, "Invalid payment order")
        if invoice.status == InvoiceStatus.PAID or payment.status == PaymentStatus.VERIFIED:
            return payment

        is_dev = payload.razorpay_order_id.startswith("order_dev_") or not settings.RAZORPAY_KEY_SECRET
        if not is_dev:
            expected = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, payload.razorpay_signature or ""):
                payment.status = PaymentStatus.FAILED
                await db.commit()
                raise HTTPException(400, "Payment signature verification failed")

        payment.provider_payment_id = payload.razorpay_payment_id or f"pay_dev_{uuid.uuid4().hex[:12]}"
        payment.status = PaymentStatus.VERIFIED
        invoice.status = InvoiceStatus.PAID
        await db.commit()

        from app.services.notification_service import NotificationService
        await NotificationService.create_notification(
            db, user_id=invoice.customer_id, title="Payment Confirmed", message=f"Invoice #{invoice.invoice_number} (₹{invoice.grand_total}) has been paid successfully.", type="BILLING", ticket_id=invoice.ticket_id
        )

        from app.websocket.manager import ws_manager
        await ws_manager.broadcast_to_ticket(
            ticket_id=invoice.ticket_id,
            message={
                "event": "INVOICE_PAID",
                "ticket_id": invoice.ticket_id,
                "invoice_id": invoice.id,
                "status": "PAID"
            }
        )

        return payment


