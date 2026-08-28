from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.core.dependencies import get_current_user_claims, RoleChecker
from app.models.responder import Responder
from app.schemas.responder import (
    ResponderRead,
    ResponderAvailabilityUpdate,
    ResponderLocationCreate,
    ResponderLocationRead,
    ResponderNearbyRead,
    ResponderPublicRead,
    ResponderAdminRead,
    SkillCreate,
    SkillRead,
)
from app.services.responder_service import ResponderService
from app.services.location_service import LocationService
from app.utils.enums import UserRole, ResponderType

router = APIRouter(prefix="/responders", tags=["Responders"])

responder_only = RoleChecker([UserRole.RESPONDER])
customer_or_staff = RoleChecker([UserRole.CUSTOMER, UserRole.MANAGER, UserRole.ADMIN])
staff_only = RoleChecker([UserRole.MANAGER, UserRole.ADMIN])


@router.get("", response_model=List[ResponderAdminRead], dependencies=[Depends(staff_only)])
async def list_responders(db: AsyncSession = Depends(get_db)):
    return [
        ResponderAdminRead(
            id=responder.id,
            user_id=responder.user_id,
            type=responder.type,
            is_available=responder.is_available,
            is_online=responder.is_online,
            full_name=responder.user.full_name,
            shop_name=responder.shop_name,
            shop_address=responder.shop_address,
            skills=[skill.skill_name for skill in responder.skills],
        )
        for responder in await ResponderService.list_responders(db)
    ]


@router.get("/nearby", response_model=List[ResponderNearbyRead], dependencies=[Depends(customer_or_staff)])
async def get_nearby_responders(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(10.0, gt=0.0, le=100.0),
    responder_type: Optional[ResponderType] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Find nearby online and available responders using Haversine distance formula.
    """
    return await ResponderService.find_nearby_responders(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        responder_type=responder_type,
    )


@router.get("/me", response_model=ResponderRead, dependencies=[Depends(responder_only)])
async def get_my_responder_profile(claims: dict = Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    return await ResponderService.get_responder_by_user_id(db, claims["user_id"])


@router.get("/{responder_id}", response_model=ResponderPublicRead, dependencies=[Depends(customer_or_staff)])
async def get_provider(responder_id: str, db: AsyncSession = Depends(get_db)):
    return await ResponderService.get_public_responder(db, responder_id)


@router.patch("/availability", response_model=ResponderRead, dependencies=[Depends(responder_only)])
async def update_responder_availability(
    update_in: ResponderAvailabilityUpdate,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle online/offline status or operational availability for the logged-in responder.
    """
    user_id = claims["user_id"]
    responder = await ResponderService.get_responder_by_user_id(db, user_id)
    return await ResponderService.update_availability(db, responder.id, update_in)


@router.patch("/location", response_model=ResponderLocationRead, dependencies=[Depends(responder_only)])
async def update_responder_location(
    location_in: ResponderLocationCreate,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    """
    Log current latitude/longitude coordinates for the logged-in responder.
    """
    user_id = claims["user_id"]
    responder = await ResponderService.get_responder_by_user_id(db, user_id)
    return await LocationService.update_responder_location(db, responder.id, location_in)


@router.post("/skills", response_model=SkillRead, dependencies=[Depends(responder_only)])
async def add_responder_skill(
    skill_in: SkillCreate,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a skill qualification tag to the logged-in responder's profile.
    """
    user_id = claims["user_id"]
    responder = await ResponderService.get_responder_by_user_id(db, user_id)
    return await ResponderService.add_skill(db, responder.id, skill_in)
