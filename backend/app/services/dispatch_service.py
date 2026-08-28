import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.responder import Responder
from app.models.responder_location import ResponderLocation
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment, AssignmentStatus
from app.utils.distance import haversine_distance


class DispatchService:
    @staticmethod
    async def find_best_responder(db: AsyncSession, ticket: Ticket):
        """Return the best eligible responder and its score without creating an assignment."""
        stmt = (
            select(Responder, ResponderLocation)
            .join(ResponderLocation, Responder.id == ResponderLocation.responder_id)
            .where(
                Responder.type == ticket.service_type,
                Responder.is_available == True,
                Responder.is_online == True,
            )
        )
        result = await db.execute(stmt)
        candidates = result.all()
        if not candidates:
            # Fallback: check if any online & available responder of this service type exists
            fallback_stmt = select(Responder).where(
                Responder.type == ticket.service_type,
                Responder.is_available == True,
                Responder.is_online == True,
            )
            fallback_res = await db.execute(fallback_stmt)
            avail = fallback_res.scalars().all()
            if avail:
                return (avail[0], 50.0)
            return None

        latest_locations = {}
        for responder, location in candidates:
            current = latest_locations.get(responder.id)
            if current is None or location.created_at > current.created_at:
                latest_locations[responder.id] = location

        scored = [
            (responder, 100.0 / max(haversine_distance(
                ticket.latitude, ticket.longitude, location.latitude, location.longitude
            ), 0.1))
            for responder in {item[0].id: item[0] for item in candidates}.values()
            for location in [latest_locations[responder.id]]
        ]
        return max(scored, key=lambda candidate: candidate[1])

    @staticmethod
    async def match_and_assign(db: AsyncSession, ticket: Ticket) -> Optional[TicketAssignment]:
        match = await DispatchService.find_best_responder(db, ticket)
        if not match:
            return None
        best_responder, best_score = match

        assignment = TicketAssignment(
            ticket_id=ticket.id,
            responder_id=best_responder.id,
            status=AssignmentStatus.OFFERED,
            score=best_score
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment
