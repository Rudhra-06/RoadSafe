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
    async def match_and_assign(db: AsyncSession, ticket: Ticket) -> Optional[TicketAssignment]:
        # Fetch active & online responders for requested service
        stmt = (
            select(Responder, ResponderLocation)
            .join(ResponderLocation, Responder.id == ResponderLocation.responder_id)
            .where(
                Responder.type == ticket.service_type,
                Responder.is_available == True,
                Responder.is_online == True
            )
        )
        result = await db.execute(stmt)
        candidates = result.all()

        if not candidates:
            return None

        scored_candidates = []
        for responder, location in candidates:
            dist = haversine_distance(
                ticket.latitude, ticket.longitude,
                location.latitude, location.longitude
            )
            # Prevent Division By Zero: Floor distance at 100 meters (0.1 km)
            effective_dist = max(dist, 0.1)
            score = 100.0 / effective_dist
            scored_candidates.append((responder, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_responder, best_score = scored_candidates[0]

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