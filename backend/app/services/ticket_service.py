from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.ticket_status_log import TicketStatusLog
from app.models.responder import Responder
from app.schemas.ticket import TicketCreate, TicketCreateResponse, TicketRead
from app.services.dispatch_service import DispatchService
from app.services.responder_service import ResponderService
from app.utils.enums import (
    TicketStatus,
    AssignmentStatus,
    VALID_TICKET_TRANSITIONS,
)
from app.websocket.manager import ws_manager


class TicketService:
    @staticmethod
    async def list_tickets_for_user(db: AsyncSession, user_id: str, role: str) -> List[Ticket]:
        query = select(Ticket).options(
            selectinload(Ticket.assignments), selectinload(Ticket.status_logs)
        ).order_by(Ticket.created_at.desc())
        if role == "CUSTOMER":
            query = query.filter(Ticket.customer_id == user_id)
        elif role == "RESPONDER":
            query = query.join(TicketAssignment).join(Responder).filter(Responder.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().unique().all()

    @staticmethod
    async def create_ticket(
        db: AsyncSession, customer_id: str, ticket_in: TicketCreate
    ) -> TicketCreateResponse:
        """
        Creates a ticket, runs auto-dispatch, triggers assignment and notifies WS clients.
        """
        ticket = Ticket(
            customer_id=customer_id,
            vehicle_type=ticket_in.vehicle_type,
            service_type=ticket_in.service_type,
            description=ticket_in.description,
            latitude=ticket_in.latitude,
            longitude=ticket_in.longitude,
            priority=ticket_in.priority,
            contact_phone=ticket_in.contact_phone,
            status=TicketStatus.REQUESTED
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

        log = TicketStatusLog(
            ticket_id=ticket.id,
            previous_status=None,
            new_status=TicketStatus.REQUESTED,
            changed_by_user_id=customer_id,
            reason="Ticket created by customer"
        )
        db.add(log)
        await db.commit()

        await TicketService._transition_status(
            db, ticket, TicketStatus.DISPATCHING, customer_id, "Automatic dispatch initiated"
        )

        dispatch_result = await DispatchService.find_best_responder(db, ticket)
        active_assignment: Optional[TicketAssignment] = None

        if dispatch_result:
            best_responder, score = dispatch_result
            
            active_assignment = TicketAssignment(
                ticket_id=ticket.id,
                responder_id=best_responder.id,
                status=AssignmentStatus.OFFERED,
                score=score
            )
            db.add(active_assignment)
            await db.commit()
            await db.refresh(active_assignment)

            await TicketService._transition_status(
                db, ticket, TicketStatus.ASSIGNED, customer_id, f"Assigned to responder {best_responder.id}"
            )

            from app.services.notification_service import NotificationService
            await NotificationService.create_notification(
                db, user_id=customer_id, title="Request Dispatched", message=f"Assistance ticket #{ticket.id[:8]} dispatched to a nearby provider.", type="DISPATCH", ticket_id=ticket.id
            )
            await NotificationService.create_notification(
                db, user_id=best_responder.user_id, title="New Job Offer", message=f"New emergency ticket #{ticket.id[:8]} ({ticket.service_type.value}) assigned to you.", type="DISPATCH", ticket_id=ticket.id
            )

            # Notify targeted responder
            await ws_manager.send_to_responder(
                responder_id=best_responder.id,
                message={
                    "event": "NEW_ASSIGNMENT",
                    "ticket_id": ticket.id,
                    "assignment_id": active_assignment.id,
                    "priority": ticket.priority.value,
                    "service_type": ticket.service_type.value,
                    "latitude": ticket.latitude,
                    "longitude": ticket.longitude,
                }
            )
        else:
            from app.services.notification_service import NotificationService
            await NotificationService.create_notification(
                db, user_id=customer_id, title="Searching for Providers", message=f"Ticket #{ticket.id[:8]} is searching for available responders.", type="DISPATCH", ticket_id=ticket.id
            )
            await TicketService._transition_status(
                db, ticket, TicketStatus.NO_RESPONDER, customer_id, "No available responders found nearby"
            )

        full_ticket = await TicketService.get_ticket_by_id(db, ticket.id)
        return TicketCreateResponse(
            ticket=TicketRead.model_validate(full_ticket),
            assignment=active_assignment
        )

    @staticmethod
    async def update_ticket_status(
        db: AsyncSession,
        ticket_id: str,
        new_status: TicketStatus,
        user_id: str,
        reason: Optional[str] = None
    ) -> Ticket:
        """
        Enforces state transition rules and broadcasts new status across ticket WS stream.
        """
        ticket = await TicketService.get_ticket_by_id(db, ticket_id)
        current_status = ticket.status

        allowed_next_states = VALID_TICKET_TRANSITIONS.get(current_status, set())
        if new_status not in allowed_next_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current_status.value}' to '{new_status.value}'."
            )

        await TicketService._transition_status(db, ticket, new_status, user_id, reason)
        return ticket

    @staticmethod
    async def assign_responder_manually(
        db: AsyncSession, ticket_id: str, responder_id: str, manager_user_id: str
    ) -> TicketAssignment:
        """
        Manual assignment override by Admin/Manager with socket notification.
        """
        ticket = await TicketService.get_ticket_by_id(db, ticket_id)

        result = await db.execute(select(Responder).filter(Responder.id == responder_id))
        responder = result.scalars().first()
        if not responder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responder not found")

        if not responder.is_available or not responder.is_online:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected responder is currently unavailable or offline"
            )

        assignment = TicketAssignment(
            ticket_id=ticket.id,
            responder_id=responder.id,
            status=AssignmentStatus.OFFERED,
            score=100.0
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        if ticket.status in (TicketStatus.REQUESTED, TicketStatus.DISPATCHING, TicketStatus.NO_RESPONDER, TicketStatus.REASSIGN):
            await TicketService._transition_status(
                db, ticket, TicketStatus.ASSIGNED, manager_user_id, f"Manually assigned to responder {responder.id}"
            )

        await ws_manager.send_to_responder(
            responder_id=responder.id,
            message={
                "event": "NEW_ASSIGNMENT",
                "ticket_id": ticket.id,
                "assignment_id": assignment.id,
                "priority": ticket.priority.value,
                "service_type": ticket.service_type.value,
            }
        )

        return assignment

    @staticmethod
    async def respond_to_assignment(
        db: AsyncSession, ticket_id: str, responder_user_id: str, accepted: bool
    ) -> TicketAssignment:
        ticket = await TicketService.get_ticket_by_id(db, ticket_id)
        responder = await ResponderService.get_responder_by_user_id(db, responder_user_id)
        result = await db.execute(select(TicketAssignment).filter(
            TicketAssignment.ticket_id == ticket_id,
            TicketAssignment.responder_id == responder.id,
            TicketAssignment.status == AssignmentStatus.OFFERED,
        ))
        assignment = result.scalars().first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No offered assignment found")
        assignment.status = AssignmentStatus.ACCEPTED if accepted else AssignmentStatus.REJECTED
        await db.commit()
        await db.refresh(assignment)
        await TicketService._transition_status(
            db, ticket,
            TicketStatus.ACCEPTED if accepted else TicketStatus.REASSIGN,
            responder_user_id,
            "Responder accepted assignment" if accepted else "Responder rejected assignment",
        )
        if accepted and ticket.customer_id:
            from app.services.notification_service import NotificationService
            await NotificationService.create_notification(
                db, user_id=ticket.customer_id, title="Mechanic Accepted", message="A technician has accepted your request and is preparing.", type="STATUS", ticket_id=ticket.id
            )
        return assignment

    @staticmethod
    async def get_ticket_by_id(db: AsyncSession, ticket_id: str) -> Ticket:
        result = await db.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.assignments),
                selectinload(Ticket.status_logs)
            )
            .filter(Ticket.id == ticket_id)
        )
        ticket = result.scalars().first()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return ticket

    @staticmethod
    async def _transition_status(
        db: AsyncSession,
        ticket: Ticket,
        new_status: TicketStatus,
        user_id: Optional[str],
        reason: Optional[str]
    ):
        prev_status = ticket.status
        ticket.status = new_status
        db.add(ticket)

        log = TicketStatusLog(
            ticket_id=ticket.id,
            previous_status=prev_status,
            new_status=new_status,
            changed_by_user_id=user_id,
            reason=reason
        )
        db.add(log)
        await db.commit()
        await db.refresh(ticket)

        # Broadcast state change to ticket channel
        await ws_manager.broadcast_to_ticket(
            ticket_id=ticket.id,
            message={
                "event": "STATUS_UPDATE",
                "ticket_id": ticket.id,
                "previous_status": prev_status.value if prev_status else None,
                "new_status": new_status.value,
                "reason": reason,
                "updated_at": ticket.updated_at.isoformat()
            }
        )

        # Create contextual persistent notification for customer
        status_notifs = {
            TicketStatus.EN_ROUTE: ("Mechanic En Route", "Your technician is on the way to your location."),
            TicketStatus.ARRIVED: ("Mechanic Arrived", "Your technician has arrived at the scene."),
            TicketStatus.IN_SERVICE: ("Service Started", "Diagnostic and repair work is underway."),
            TicketStatus.COMPLETED: ("Service Resolved", "Your roadside assistance has been completed."),
        }
        if new_status in status_notifs and ticket.customer_id:
            from app.services.notification_service import NotificationService
            title, msg = status_notifs[new_status]
            await NotificationService.create_notification(
                db, user_id=ticket.customer_id, title=title, message=msg, type="STATUS", ticket_id=ticket.id
            )
