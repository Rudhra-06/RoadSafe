from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.db.database import get_db
from app.models.billing import Review
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.responder import Responder
from app.schemas.billing import ReviewCreate, ReviewRead
from app.utils.enums import AssignmentStatus, TicketStatus, UserRole

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewCreate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    if claims["role"] != UserRole.CUSTOMER.value:
        raise HTTPException(403, "Only customers can submit reviews")
    ticket = (await db.execute(select(Ticket).where(Ticket.id == payload.ticket_id, Ticket.customer_id == claims["user_id"]))).scalars().first()
    if not ticket or ticket.status != TicketStatus.COMPLETED:
        raise HTTPException(400, "A completed customer ticket is required")
    if (await db.execute(select(Review).where(Review.ticket_id == ticket.id))).scalars().first():
        raise HTTPException(409, "A review already exists for this ticket")
    assignment = (await db.execute(select(TicketAssignment).where(TicketAssignment.ticket_id == ticket.id, TicketAssignment.status == AssignmentStatus.ACCEPTED))).scalars().first()
    review = Review(
        ticket_id=ticket.id,
        customer_id=claims["user_id"],
        responder_id=assignment.responder_id if assignment else None,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review

@router.get("", response_model=list[ReviewRead], dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Review).order_by(Review.created_at.desc()))).scalars().all()

@router.get("/stats", dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))])
async def get_review_stats(db: AsyncSession = Depends(get_db)):
    reviews = (await db.execute(select(Review).order_by(Review.created_at.desc()))).scalars().all()
    total_reviews = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 2) if total_reviews else 0.0

    # Group by responder
    responder_map = {}
    for r in reviews:
        rid = r.responder_id or "unassigned"
        if rid not in responder_map:
            responder_map[rid] = {"ratings": [], "count": 0}
        responder_map[rid]["ratings"].append(r.rating)
        responder_map[rid]["count"] += 1

    responder_stats = {}
    for rid, data in responder_map.items():
        responder_stats[rid] = {
            "average_rating": round(sum(data["ratings"]) / data["count"], 2),
            "review_count": data["count"]
        }

    return {
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
        "responder_breakdown": responder_stats,
        "recent_reviews": [ReviewRead.model_validate(r) for r in reviews[:10]]
    }

@router.get("/responders/{responder_id}", response_model=list[ReviewRead])
async def get_responder_reviews(responder_id: str, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Review).where(Review.responder_id == responder_id).order_by(Review.created_at.desc()))).scalars().all()
