from datetime import datetime
import math
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.responder import Responder
from app.models.responder_location import ResponderLocation
from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.utils.enums import AssignmentStatus, TicketStatus, ResponderType
from app.utils.distance import haversine_distance


class DispatchService:
    @staticmethod
    async def find_best_responder(
        db: AsyncSession,
        ticket: Ticket,
        exclude_responder_ids: Optional[Set[str]] = None
    ):
        """
        Return the best eligible responder within the configured service radius and their score/distance without creating an assignment.
        Filters for:
        - Responder is_available == True, is_online == True
        - Responder type or skills match ticket service_type
        - Responder not in exclude_responder_ids (e.g. previously declined this ticket)
        - Responder not currently busy on an active accepted job
        - Responder has a fresh, valid location within DISPATCH_RADIUS_KM
        - Nearest eligible worker within radius is selected
        """
        if exclude_responder_ids is None:
            exclude_responder_ids = set()
        else:
            exclude_responder_ids = set(exclude_responder_ids)

        print(f"[DISPATCH START] ticket_id={ticket.id}")
        print(f"[DISPATCH LOCATION]\nCustomer: {ticket.latitude}, {ticket.longitude}")

        # Exclude responders who are currently busy with an active accepted ticket
        busy_stmt = (
            select(TicketAssignment.responder_id)
            .join(Ticket, TicketAssignment.ticket_id == Ticket.id)
            .where(
                TicketAssignment.status == AssignmentStatus.ACCEPTED,
                Ticket.status.in_([
                    TicketStatus.ACCEPTED,
                    TicketStatus.EN_ROUTE,
                    TicketStatus.ARRIVED,
                    TicketStatus.IN_SERVICE,
                ])
            )
        )
        busy_res = await db.execute(busy_stmt)
        busy_responder_ids = set(busy_res.scalars().all())

        # Fetch all responders with users, skills, and locations loaded
        stmt = select(Responder).options(
            selectinload(Responder.user),
            selectinload(Responder.skills),
            selectinload(Responder.locations)
        )
        result = await db.execute(stmt)
        all_responders = result.scalars().all()

        eligible_candidates = []

        for resp in all_responders:
            resp_name = resp.user.full_name if resp.user else f"Responder_{resp.id[:6]}"

            # Check 1: Previously declined / excluded
            if resp.id in exclude_responder_ids:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: PREVIOUSLY_DECLINED")
                continue

            # Check 2: Busy on active accepted job
            if resp.id in busy_responder_ids:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: BUSY")
                continue

            # Check 3: Online status
            if not resp.is_online:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: OFFLINE")
                continue

            # Check 4: Availability status
            if not resp.is_available:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: NOT_AVAILABLE")
                continue

            # Check 5: Service Type & Skill Compatibility
            type_match = (resp.type == ticket.service_type)
            general_match = (resp.type in [ResponderType.ROADSIDE_TECHNICIAN, ResponderType.CAR_MECHANIC])
            
            skill_names = [s.skill_name.upper() for s in resp.skills] if resp.skills else []
            skill_match = any(
                kw in " ".join(skill_names) or any(kw in s for s in skill_names)
                for kw in [ticket.service_type.value, "TYRE", "TIRE", "ENGINE", "BATTERY", "TOWING", "MAINTENANCE", "GENERAL", "MECHANIC"]
            )

            if not (type_match or general_match or skill_match):
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: WRONG_SKILL")
                continue

            # Check 6: Location coordinates and fresh timestamp
            latest_loc = max(resp.locations, key=lambda l: l.created_at) if resp.locations else None
            if not latest_loc:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: NO_LOCATION")
                continue

            # Check 7: Stale location check
            loc_age = (datetime.utcnow() - latest_loc.created_at).total_seconds()
            print(f"[RESPONDER LOCATION]\nWorker: {resp.id}\nLocation: {latest_loc.latitude}, {latest_loc.longitude}\nLocation Age: {int(loc_age)}s")

            if loc_age > settings.DISPATCH_LOCATION_MAX_AGE_SECONDS:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: STALE_LOCATION")
                continue

            # Check 8: Service radius check (Haversine distance)
            dist = haversine_distance(ticket.latitude, ticket.longitude, latest_loc.latitude, latest_loc.longitude)
            print(f"[DISPATCH DISTANCE]\nWorker: {resp.id}\nDistance: {dist:.2f} km\nRadius: {settings.DISPATCH_RADIUS_KM} km")

            if dist > settings.DISPATCH_RADIUS_KM:
                print(f"[DISPATCH REJECTED]\nWorker: {resp.id}\nReason: OUTSIDE_SERVICE_RADIUS")
                continue

            score = 100.0 / max(dist, 0.1)
            print(f"[DISPATCH ELIGIBLE]\nWorker: {resp.id}")
            eligible_candidates.append((resp, score, dist))

        if not eligible_candidates:
            print(f"[DISPATCH RESULT]\nSelected Worker: NONE\nReason: No eligible workers within service radius")
            return None

        # Select nearest eligible worker (highest score corresponds to lowest distance)
        best = max(eligible_candidates, key=lambda x: x[1])
        print(f"[DISPATCH RESULT]\nSelected Worker: {best[0].id}\nDistance: {best[2]:.2f} km")
        return (best[0], best[1])


    @staticmethod
    async def match_and_assign(
        db: AsyncSession, ticket: Ticket, exclude_responder_ids: Optional[Set[str]] = None
    ) -> Optional[TicketAssignment]:
        match = await DispatchService.find_best_responder(db, ticket, exclude_responder_ids)
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


