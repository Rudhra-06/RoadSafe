import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections subscribed to ticket streams, responder notifications, or admin operations.
    """

    def __init__(self):
        # Map ticket_id -> list of connected WebSockets
        self.ticket_connections: Dict[str, List[WebSocket]] = {}
        # Map responder_id -> list of connected WebSockets
        self.responder_connections: Dict[str, List[WebSocket]] = {}
        # List of connected Admin WebSockets for real-time operations console
        self.admin_connections: List[WebSocket] = []

    async def connect_ticket(self, websocket: WebSocket, ticket_id: str):
        await websocket.accept()
        if ticket_id not in self.ticket_connections:
            self.ticket_connections[ticket_id] = []
        self.ticket_connections[ticket_id].append(websocket)

    def disconnect_ticket(self, websocket: WebSocket, ticket_id: str):
        if ticket_id in self.ticket_connections:
            if websocket in self.ticket_connections[ticket_id]:
                self.ticket_connections[ticket_id].remove(websocket)
            if not self.ticket_connections[ticket_id]:
                del self.ticket_connections[ticket_id]

    async def connect_responder(self, websocket: WebSocket, responder_id: str):
        await websocket.accept()
        if responder_id not in self.responder_connections:
            self.responder_connections[responder_id] = []
        self.responder_connections[responder_id].append(websocket)

    def disconnect_responder(self, websocket: WebSocket, responder_id: str):
        if responder_id in self.responder_connections:
            if websocket in self.responder_connections[responder_id]:
                self.responder_connections[responder_id].remove(websocket)
            if not self.responder_connections[responder_id]:
                del self.responder_connections[responder_id]

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def broadcast_to_admin(self, message: dict):
        """
        Sends operational JSON event to connected admin executive consoles.
        """
        disconnected: List[WebSocket] = []
        for connection in self.admin_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect_admin(conn)

    async def broadcast_to_ticket(self, ticket_id: str, message: dict):
        """
        Sends JSON message to all subscribers listening on a specific ticket and notifies admin.
        """
        if ticket_id in self.ticket_connections:
            disconnected: List[WebSocket] = []
            for connection in self.ticket_connections[ticket_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.disconnect_ticket(conn, ticket_id)

        # Mirror operational ticket updates to active admin console
        await self.broadcast_to_admin(message)

    async def send_to_responder(self, responder_id: str, message: dict):
        """
        Sends JSON notification directly to connected client sockets for a responder and notifies admin.
        """
        if responder_id in self.responder_connections:
            disconnected: List[WebSocket] = []
            for connection in self.responder_connections[responder_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.disconnect_responder(conn, responder_id)

        # Mirror dispatch offer events to admin console
        await self.broadcast_to_admin(message)


ws_manager = ConnectionManager()