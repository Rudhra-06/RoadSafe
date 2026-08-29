from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.db.database import get_db
from app.schemas.billing import JobCompletionCreate, InvoiceRead, RazorpayOrderRead, RazorpayVerifyRequest, PaymentRead
from app.services.billing_service import BillingService
from app.utils.enums import UserRole
from app.core.config import settings

router = APIRouter(tags=["Billing and Payments"])
staff = RoleChecker([UserRole.RESPONDER, UserRole.ADMIN, UserRole.MANAGER])
admin = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])

@router.post("/billing/tickets/{ticket_id}/complete", response_model=InvoiceRead, dependencies=[Depends(staff)])
@router.post("/tickets/{ticket_id}/complete", response_model=InvoiceRead, dependencies=[Depends(staff)])
async def complete_job(ticket_id: str, payload: JobCompletionCreate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    return await BillingService.create_invoice_for_completion(db, ticket_id, claims["user_id"], payload)

@router.get("/invoices", response_model=list[InvoiceRead])
@router.get("/billing/invoices", response_model=list[InvoiceRead])
async def list_invoices(claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    return await BillingService.list_invoices(db, claims["user_id"] if claims["role"] == UserRole.CUSTOMER.value else None)

@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
@router.get("/billing/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(invoice_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    print(f"[INVOICE LOAD]\nInvoice ID: {invoice_id}")
    user_id = claims.get("user_id")
    print(f"[INVOICE QUERY]\nCustomer ID: {user_id}")
    try:
        invoice = await BillingService.get_invoice(db, invoice_id)
        print("[INVOICE RESULT]\nFound: true")
    except HTTPException as e:
        if e.status_code == 404:
            print("[INVOICE RESULT]\nFound: false")
        raise e

    if claims["role"] == UserRole.CUSTOMER.value and invoice.customer_id != user_id:
        print("[INVOICE AUTH]\nAuthorized: false")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invoice access denied")
    
    print("[INVOICE AUTH]\nAuthorized: true")
    return invoice

@router.get("/tickets/{ticket_id}/invoice", response_model=InvoiceRead)
@router.get("/billing/tickets/{ticket_id}/invoice", response_model=InvoiceRead)
async def get_ticket_invoice(ticket_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    print(f"[INVOICE LOAD]\nInvoice ID: {ticket_id}")
    user_id = claims.get("user_id")
    print(f"[INVOICE QUERY]\nCustomer ID: {user_id}")
    try:
        invoice = await BillingService.get_invoice(db, ticket_id)
        print("[INVOICE RESULT]\nFound: true")
    except HTTPException as e:
        if e.status_code == 404:
            print("[INVOICE RESULT]\nFound: false")
        raise e

    if claims["role"] == UserRole.CUSTOMER.value and invoice.customer_id != user_id:
        print("[INVOICE AUTH]\nAuthorized: false")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invoice access denied")
    
    print("[INVOICE AUTH]\nAuthorized: true")
    return invoice

@router.post("/billing/invoices/{invoice_id}/payment-order", response_model=RazorpayOrderRead)
@router.post("/invoices/{invoice_id}/payment-order", response_model=RazorpayOrderRead)
async def payment_order(invoice_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    print(f"[INVOICE LOAD]\nInvoice ID: {invoice_id}")
    user_id = claims.get("user_id")
    print(f"[INVOICE QUERY]\nCustomer ID: {user_id}")
    try:
        invoice = await BillingService.get_invoice(db, invoice_id)
        print("[INVOICE RESULT]\nFound: true")
    except HTTPException as e:
        if e.status_code == 404:
            print("[INVOICE RESULT]\nFound: false")
        raise e

    if claims["role"] == UserRole.CUSTOMER.value and invoice.customer_id != user_id:
        print("[INVOICE AUTH]\nAuthorized: false")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invoice access denied")
    
    print("[INVOICE AUTH]\nAuthorized: true")
    payment = await BillingService.create_payment_order(db, invoice)
    return RazorpayOrderRead(
        invoice_id=invoice.id,
        order_id=payment.provider_order_id,
        amount=int(payment.amount * 100),
        currency=payment.currency,
        key_id=settings.RAZORPAY_KEY_ID or "rzp_test_key"
    )

@router.post("/billing/invoices/{invoice_id}/verify-payment", response_model=PaymentRead)
@router.post("/invoices/{invoice_id}/verify-payment", response_model=PaymentRead)
async def verify_payment(invoice_id: str, payload: RazorpayVerifyRequest, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    print(f"[INVOICE LOAD]\nInvoice ID: {invoice_id}")
    user_id = claims.get("user_id")
    print(f"[INVOICE QUERY]\nCustomer ID: {user_id}")
    try:
        invoice = await BillingService.get_invoice(db, invoice_id)
        print("[INVOICE RESULT]\nFound: true")
    except HTTPException as e:
        if e.status_code == 404:
            print("[INVOICE RESULT]\nFound: false")
        raise e

    if claims["role"] == UserRole.CUSTOMER.value and invoice.customer_id != user_id:
        print("[INVOICE AUTH]\nAuthorized: false")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invoice access denied")
    
    print("[INVOICE AUTH]\nAuthorized: true")
    return await BillingService.verify_payment(db, invoice, payload)


