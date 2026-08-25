from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/tickets/{ticket_id}")
async def ticket_websocket_endpoint(websocket: WebSocket, ticket_id: str):
    """
    Subscribes client to live ticket status changes and responder location streams.
    """
    await ws_manager.connect_ticket(websocket, ticket_id)
    try:
        while True:
            # Keep connection alive & accept client heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_ticket(websocket, ticket_id)


@router.websocket("/responders/{responder_id}")
async def responder_websocket_endpoint(websocket: WebSocket, responder_id: str):
    """
    Subscribes responder to immediate dynamic assignment offers and job notifications.
    """
    await ws_manager.connect_responder(websocket, responder_id)
    try:
        while True:
            # Keep connection alive & accept client heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_responder(websocket, responder_id)