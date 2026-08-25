from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.dependencies import get_current_user_claims
from app.schemas.offline import OfflineSyncRequest, OfflineSyncResponse
from app.services.offline_sync_service import OfflineSyncService

router = APIRouter(prefix="/offline", tags=["Offline Sync"])


@router.post("/sync", response_model=OfflineSyncResponse, status_code=status.HTTP_200_OK)
async def sync_offline_actions(
    sync_req: OfflineSyncRequest,
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronizes offline actions accumulated during network dropouts with idempotency tracking.
    """
    user_id = claims["user_id"]
    return await OfflineSyncService.process_sync(db, user_id, sync_req)