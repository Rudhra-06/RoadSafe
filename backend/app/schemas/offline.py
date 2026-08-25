from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class OfflineActionItem(BaseModel):
    idempotency_key: str = Field(..., description="Unique client-generated UUID for deduplication")
    action_type: str = Field(..., description="LOCATION_UPDATE or STATUS_UPDATE")
    payload: Dict[str, Any] = Field(..., description="Action parameters")
    client_timestamp: str = Field(..., description="ISO 8601 timestamp when action was recorded offline")


class OfflineSyncRequest(BaseModel):
    actions: List[OfflineActionItem] = Field(..., description="Ordered queue of offline actions")


class OfflineActionResult(BaseModel):
    idempotency_key: str
    action_type: str
    status: str = Field(..., description="SUCCESS, DUPLICATE_SKIPPED, or FAILED")
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class OfflineSyncResponse(BaseModel):
    processed_count: int
    skipped_count: int
    failed_count: int
    results: List[OfflineActionResult]