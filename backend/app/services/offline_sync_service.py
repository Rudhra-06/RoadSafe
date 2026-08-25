from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.idempotency import IdempotencyRecord
from app.schemas.offline import OfflineSyncRequest, OfflineSyncResponse, OfflineActionResult
from app.schemas.responder import ResponderLocationCreate
from app.services.location_service import LocationService
from app.services.ticket_service import TicketService
from app.services.responder_service import ResponderService
from app.utils.enums import TicketStatus


class OfflineSyncService:
    @staticmethod
    async def process_sync(
        db: AsyncSession, user_id: str, sync_req: OfflineSyncRequest
    ) -> OfflineSyncResponse:
        results = []
        processed_count = 0
        skipped_count = 0
        failed_count = 0

        for item in sync_req.actions:
            # Check for existing idempotency record
            existing_res = await db.execute(
                select(IdempotencyRecord).filter(
                    IdempotencyRecord.idempotency_key == item.idempotency_key
                )
            )
            existing_record = existing_res.scalars().first()

            if existing_record:
                skipped_count += 1
                results.append(
                    OfflineActionResult(
                        idempotency_key=item.idempotency_key,
                        action_type=item.action_type,
                        status="DUPLICATE_SKIPPED",
                        message="Action already processed previously",
                        data=existing_record.response_payload
                    )
                )
                continue

            # Process action based on action_type
            try:
                action_data = await OfflineSyncService._execute_action(
                    db, user_id, item.action_type, item.payload
                )

                # Store Idempotency Record
                record = IdempotencyRecord(
                    idempotency_key=item.idempotency_key,
                    user_id=user_id,
                    action_type=item.action_type,
                    response_payload=action_data
                )
                db.add(record)
                await db.commit()

                processed_count += 1
                results.append(
                    OfflineActionResult(
                        idempotency_key=item.idempotency_key,
                        action_type=item.action_type,
                        status="SUCCESS",
                        data=action_data
                    )
                )

            except Exception as e:
                failed_count += 1
                results.append(
                    OfflineActionResult(
                        idempotency_key=item.idempotency_key,
                        action_type=item.action_type,
                        status="FAILED",
                        message=str(e)
                    )
                )

        return OfflineSyncResponse(
            processed_count=processed_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results
        )

    @staticmethod
    async def _execute_action(
        db: AsyncSession, user_id: str, action_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if action_type == "LOCATION_UPDATE":
            responder = await ResponderService.get_responder_by_user_id(db, user_id)
            loc_in = ResponderLocationCreate(
                latitude=payload["latitude"],
                longitude=payload["longitude"]
            )
            location_res = await LocationService.update_responder_location(db, responder.id, loc_in)
            return location_res.model_dump()

        elif action_type == "STATUS_UPDATE":
            ticket_id = payload["ticket_id"]
            new_status = TicketStatus(payload["new_status"])
            reason = payload.get("reason", "Offline sync status update")
            
            ticket = await TicketService.update_ticket_status(
                db, ticket_id, new_status, user_id, reason
            )
            return {"ticket_id": ticket.id, "status": ticket.status.value}

        else:
            raise ValueError(f"Unsupported offline action type: {action_type}")