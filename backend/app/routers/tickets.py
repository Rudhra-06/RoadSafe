from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.schemas.ticket import (
    TicketCreate,
    TicketCreateResponse,
    TicketRead,
    TicketStatusUpdate,
    TicketAssignRequest,
    AssignmentDecision,
    AssignmentRead
)
from app.services.ticket_service import TicketService
from app.utils.enums import UserRole
from app.models.ticket_assignment import TicketAssignment
from app.models.responder import Responder

router = APIRouter(prefix="/tickets", tags=["Tickets"])

customer_or_staff = RoleChecker([UserRole.CUSTOMER, UserRole.MANAGER, UserRole.ADMIN])
manager_or_admin = RoleChecker([UserRole.MANAGER, UserRole.ADMIN])
responder_only = RoleChecker([UserRole.RESPONDER])


async def _can_access_ticket(db, ticket, claims):
    role = claims["role"]
    if role in (UserRole.ADMIN.value, UserRole.MANAGER.value) or ticket.customer_id == claims["user_id"]:
        return True
    result = await db.execute(
        select(TicketAssignment.id).join(Responder).where(
            TicketAssignment.ticket_id == ticket.id,
            Responder.user_id == claims["user_id"],
        )
    )
    return result.scalar_one_or_none() is not None


@router.get("", response_model=list[TicketRead])
async def list_tickets(
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    """List tickets visible to the signed-in customer, responder, manager, or admin."""
    return await TicketService.list_tickets_for_user(db, claims["user_id"], claims["role"])


@router.post("", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a roadside assistance request. Automatically triggers dispatch matching.
    """
    customer_id = claims["user_id"]
    return await TicketService.create_ticket(db, customer_id, ticket_in)


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: str,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve full details for a ticket, including state transition logs and assignments.
    """
    ticket = await TicketService.get_ticket_by_id(db, ticket_id)
    if not await _can_access_ticket(db, ticket, claims):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot access this ticket")
    return ticket


@router.patch("/{ticket_id}/status", response_model=TicketRead)
async def update_ticket_status(
    ticket_id: str,
    status_update: TicketStatusUpdate,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Update ticket status. Validates transition against the frozen state machine rules.
    """
    user_id = claims["user_id"]
    ticket = await TicketService.get_ticket_by_id(db, ticket_id)
    if not await _can_access_ticket(db, ticket, claims):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this ticket")
    updated_ticket = await TicketService.update_ticket_status(
        db, ticket_id, status_update.status, user_id, status_update.reason
    )
    return updated_ticket


@router.post("/{ticket_id}/assignment/respond", response_model=AssignmentRead, dependencies=[Depends(responder_only)])
async def respond_to_assignment(
    ticket_id: str,
    decision: AssignmentDecision,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    """Accept or reject the logged-in responder's offered assignment."""
    return await TicketService.respond_to_assignment(db, ticket_id, claims["user_id"], decision.accepted)


@router.post("/{ticket_id}/assign", response_model=AssignmentRead, dependencies=[Depends(manager_or_admin)])
async def assign_ticket_manually(
    ticket_id: str,
    assign_req: TicketAssignRequest,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually assign or reassign a responder to a ticket (Manager/Admin only).
    """
    manager_user_id = claims["user_id"]
    assignment = await TicketService.assign_responder_manually(
        db, ticket_id, assign_req.responder_id, manager_user_id
    )
    return assignment
