from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.db.database import get_db
from app.models.billing import Review
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.schemas.billing import ReviewCreate, ReviewRead
from app.utils.enums import AssignmentStatus, TicketStatus, UserRole

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewCreate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    if claims["role"] != UserRole.CUSTOMER.value: raise HTTPException(403, "Only customers can submit reviews")
    ticket = (await db.execute(select(Ticket).where(Ticket.id == payload.ticket_id, Ticket.customer_id == claims["user_id"]))).scalars().first()
    if not ticket or ticket.status != TicketStatus.COMPLETED: raise HTTPException(400, "A completed customer ticket is required")
    if (await db.execute(select(Review).where(Review.ticket_id == ticket.id))).scalars().first(): raise HTTPException(409, "A review already exists for this ticket")
    assignment = (await db.execute(select(TicketAssignment).where(TicketAssignment.ticket_id == ticket.id, TicketAssignment.status == AssignmentStatus.ACCEPTED))).scalars().first()
    review = Review(ticket_id=ticket.id, customer_id=claims["user_id"], responder_id=assignment.responder_id if assignment else None, rating=payload.rating, comment=payload.comment)
    db.add(review); await db.commit(); await db.refresh(review); return review

@router.get("", response_model=list[ReviewRead], dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Review).order_by(Review.created_at.desc()))).scalars().all()
