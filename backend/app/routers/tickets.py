from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.schemas.ticket import (
    TicketCreate,
    TicketCreateResponse,
    TicketRead,
    TicketStatusUpdate,
    TicketAssignRequest,
    AssignmentRead
)
from app.services.ticket_service import TicketService
from app.utils.enums import UserRole

router = APIRouter(prefix="/tickets", tags=["Tickets"])

customer_or_staff = RoleChecker([UserRole.CUSTOMER, UserRole.MANAGER, UserRole.ADMIN])
manager_or_admin = RoleChecker([UserRole.MANAGER, UserRole.ADMIN])


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
    updated_ticket = await TicketService.update_ticket_status(
        db, ticket_id, status_update.status, user_id, status_update.reason
    )
    return updated_ticket


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