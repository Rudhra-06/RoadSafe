from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.responder_location import ResponderLocation
from app.models.ticket_assignment import TicketAssignment
from app.schemas.responder import ResponderLocationCreate, ResponderLocationRead
from app.utils.enums import AssignmentStatus
from app.websocket.manager import ws_manager


class LocationService:
    @staticmethod
    async def update_responder_location(
        db: AsyncSession, responder_id: str, location_in: ResponderLocationCreate
    ) -> ResponderLocationRead:
        """
        Record a new GPS log for a responder and broadcast to active ticket stream if assigned.
        """
        location_record = ResponderLocation(
            responder_id=responder_id,
            latitude=location_in.latitude,
            longitude=location_in.longitude,
        )
        db.add(location_record)
        await db.commit()
        await db.refresh(location_record)

        # Find active ticket assignments for this responder
        assignment_res = await db.execute(
            select(TicketAssignment)
            .filter(
                TicketAssignment.responder_id == responder_id,
                TicketAssignment.status.in_([AssignmentStatus.OFFERED, AssignmentStatus.ACCEPTED])
            )
        )
        active_assignments = assignment_res.scalars().all()

        for assignment in active_assignments:
            await ws_manager.broadcast_to_ticket(
                ticket_id=assignment.ticket_id,
                message={
                    "event": "LOCATION_UPDATE",
                    "responder_id": responder_id,
                    "ticket_id": assignment.ticket_id,
                    "latitude": location_in.latitude,
                    "longitude": location_in.longitude,
                    "timestamp": location_record.created_at.isoformat()
                }
            )

        return ResponderLocationRead.model_validate(location_record)

    @staticmethod
    async def get_latest_responder_location(
        db: AsyncSession, responder_id: str
    ) -> Optional[Tuple[float, float, datetime]]:
        """
        Retrieve the most recent latitude, longitude, and timestamp logged by a responder.
        """
        result = await db.execute(
            select(ResponderLocation)
            .filter(ResponderLocation.responder_id == responder_id)
            .order_by(ResponderLocation.created_at.desc())
            .limit(1)
        )
        location = result.scalars().first()
        if location:
            return (location.latitude, location.longitude, location.created_at)
        return None