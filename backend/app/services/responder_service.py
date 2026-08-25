from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.responder import Responder
from app.models.responder_skill import ResponderSkill
from app.models.responder_location import ResponderLocation
from app.schemas.responder import (
    ResponderRead,
    ResponderAvailabilityUpdate,
    ResponderNearbyRead,
    SkillCreate,
    SkillRead,
)
from app.utils.distance import haversine_distance
from app.utils.enums import ResponderType
from app.websocket.manager import ws_manager


class ResponderService:
    @staticmethod
    async def get_responder_by_user_id(db: AsyncSession, user_id: str) -> Responder:
        """
        Fetch responder record linked to a given User ID.
        """
        result = await db.execute(
            select(Responder)
            .options(
                selectinload(Responder.skills),
                selectinload(Responder.locations),
            )
            .filter(Responder.user_id == user_id)
        )
        responder = result.scalars().first()
        if not responder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Responder profile not found for current user",
            )
        return responder

    @staticmethod
    async def update_availability(
        db: AsyncSession, responder_id: str, update_in: ResponderAvailabilityUpdate
    ) -> ResponderRead:
        """
        Update is_available and/or is_online flags for a responder and send socket update.
        """
        result = await db.execute(
            select(Responder)
            .options(selectinload(Responder.skills))
            .filter(Responder.id == responder_id)
        )
        responder = result.scalars().first()
        if not responder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Responder profile not found",
            )

        if update_in.is_available is not None:
            responder.is_available = update_in.is_available
        if update_in.is_online is not None:
            responder.is_online = update_in.is_online

        await db.commit()
        await db.refresh(responder)

        # Notify responder socket channel
        await ws_manager.send_to_responder(
            responder_id=responder_id,
            message={
                "event": "AVAILABILITY_UPDATE",
                "responder_id": responder_id,
                "is_available": responder.is_available,
                "is_online": responder.is_online
            }
        )

        return ResponderRead.model_validate(responder)

    @staticmethod
    async def find_nearby_responders(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        responder_type: Optional[ResponderType] = None,
    ) -> List[ResponderNearbyRead]:
        """
        Queries active and available responders, computes their distance using Haversine,
        and filters within the specified radius_km.
        """
        query = select(Responder).filter(
            Responder.is_available == True,
            Responder.is_online == True,
        )
        if responder_type:
            query = query.filter(Responder.type == responder_type)

        result = await db.execute(query)
        responders = result.scalars().all()

        nearby_responders: List[ResponderNearbyRead] = []

        for responder in responders:
            loc_result = await db.execute(
                select(ResponderLocation)
                .filter(ResponderLocation.responder_id == responder.id)
                .order_by(ResponderLocation.created_at.desc())
                .limit(1)
            )
            latest_loc = loc_result.scalars().first()
            if not latest_loc:
                continue

            dist = haversine_distance(
                latitude, longitude, latest_loc.latitude, latest_loc.longitude
            )
            if dist <= radius_km:
                nearby_responders.append(
                    ResponderNearbyRead(
                        responder_id=responder.id,
                        user_id=responder.user_id,
                        type=responder.type,
                        latitude=latest_loc.latitude,
                        longitude=latest_loc.longitude,
                        distance_km=dist,
                        is_available=responder.is_available,
                    )
                )

        nearby_responders.sort(key=lambda x: x.distance_km)
        return nearby_responders

    @staticmethod
    async def add_skill(
        db: AsyncSession, responder_id: str, skill_in: SkillCreate
    ) -> SkillRead:
        """
        Add a qualification skill to a responder profile.
        """
        skill = ResponderSkill(
            responder_id=responder_id,
            skill_name=skill_in.skill_name.strip().upper(),
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return SkillRead.model_validate(skill)