from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.responder import Responder
from app.models.responder_location import ResponderLocation
from app.models.ticket import Ticket
from app.utils.distance import haversine_distance
from app.utils.enums import TicketPriority


class DispatchService:
    @staticmethod
    async def find_best_responder(
        db: AsyncSession, ticket: Ticket
    ) -> Optional[Tuple[Responder, float]]:
        """
        Calculates dispatch scores for online & available responders matching service type.
        Ranking factors:
        1. Distance score (closer = higher)
        2. Priority multiplier (Emergency gets boost)
        3. Skill match bonus
        Returns tuple of (Best Responder, Dispatch Score) or None.
        """
        # Fetch candidate responders matching requested service type
        query = (
            select(Responder)
            .options(
                selectinload(Responder.skills),
                selectinload(Responder.user)
            )
            .filter(
                Responder.type == ticket.service_type,
                Responder.is_available == True,
                Responder.is_online == True
            )
        )
        result = await db.execute(query)
        candidates: List[Responder] = result.scalars().all()

        if not candidates:
            return None

        scored_candidates: List[Tuple[Responder, float]] = []

        # Priority weight multiplier
        priority_multiplier = {
            TicketPriority.LOW: 1.0,
            TicketPriority.MEDIUM: 1.2,
            TicketPriority.HIGH: 1.5,
            TicketPriority.EMERGENCY: 2.0
        }.get(ticket.priority, 1.0)

        for responder in candidates:
            # Fetch latest location
            loc_result = await db.execute(
                select(ResponderLocation)
                .filter(ResponderLocation.responder_id == responder.id)
                .order_by(ResponderLocation.created_at.desc())
                .limit(1)
            )
            latest_loc = loc_result.scalars().first()
            if not latest_loc:
                continue

            # Calculate Haversine distance in KM
            dist_km = haversine_distance(
                ticket.latitude, ticket.longitude,
                latest_loc.latitude, latest_loc.longitude
            )

            # Cap max effective distance for scoring at 50km
            if dist_km > 50.0:
                continue

            # Distance Score: 100 max score, decreases as distance increases
            base_distance_score = max(0.0, 100.0 - (dist_km * 2.0))

            # Skill Bonus: Check if responder has explicit matching skill strings
            has_matching_skill = any(
                skill.skill_name.upper() in ticket.service_type.value.upper()
                for skill in responder.skills
            )
            skill_bonus = 15.0 if has_matching_skill else 0.0

            # Final Score Calculation
            total_score = (base_distance_score + skill_bonus) * priority_multiplier
            scored_candidates.append((responder, round(total_score, 2)))

        if not scored_candidates:
            return None

        # Sort by total score descending
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        return scored_candidates[0]