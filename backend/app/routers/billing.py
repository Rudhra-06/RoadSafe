from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.db.database import get_db
from app.schemas.billing import JobCompletionCreate, InvoiceRead, RazorpayOrderRead, RazorpayVerifyRequest, PaymentRead
from app.services.billing_service import BillingService
from app.utils.enums import UserRole

router = APIRouter(prefix="/billing", tags=["Billing and Payments"])
staff = RoleChecker([UserRole.RESPONDER, UserRole.ADMIN, UserRole.MANAGER])
admin = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])

@router.post("/tickets/{ticket_id}/complete", response_model=InvoiceRead, dependencies=[Depends(staff)])
async def complete_job(ticket_id: str, payload: JobCompletionCreate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    return await BillingService.create_invoice_for_completion(db, ticket_id, claims["user_id"], payload)

@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    return await BillingService.list_invoices(db, claims["user_id"] if claims["role"] == UserRole.CUSTOMER.value else None)

@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(invoice_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    invoice = await BillingService.get_invoice(db, invoice_id)
    if claims["role"] == UserRole.CUSTOMER.value and invoice.customer_id != claims["user_id"]: raise __import__('fastapi').HTTPException(403, "Invoice access denied")
    return invoice

@router.post("/invoices/{invoice_id}/payment-order", response_model=RazorpayOrderRead)
async def payment_order(invoice_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    invoice = await BillingService.get_invoice(db, invoice_id)
    if invoice.customer_id != claims["user_id"]: raise __import__('fastapi').HTTPException(403, "Invoice access denied")
    payment = await BillingService.create_payment_order(db, invoice)
    from app.core.config import settings
    return RazorpayOrderRead(invoice_id=invoice.id, order_id=payment.provider_order_id, amount=int(payment.amount * 100), currency=payment.currency, key_id=settings.RAZORPAY_KEY_ID)

@router.post("/invoices/{invoice_id}/verify-payment", response_model=PaymentRead)
async def verify_payment(invoice_id: str, payload: RazorpayVerifyRequest, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    invoice = await BillingService.get_invoice(db, invoice_id)
    if invoice.customer_id != claims["user_id"]: raise __import__('fastapi').HTTPException(403, "Invoice access denied")
    return await BillingService.verify_payment(db, invoice, payload)
