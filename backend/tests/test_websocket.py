import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_ticket_stream_connection():
    client = TestClient(app)
    ticket_id = "test-ticket-id-999"
    with client.websocket_connect(f"/ws/tickets/{ticket_id}") as websocket:
        websocket.send_text("ping")
        # Connection established without exception
        assert websocket is not None