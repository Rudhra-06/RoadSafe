import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ticket_lifecycle_and_state_machine(client: AsyncClient):
    # Setup Customer
    await client.post("/api/v1/auth/register", json={
        "email": "cust_dispatch@roadsafe.com",
        "password": "Password123!",
        "full_name": "Ticket Tester",
        "role": "CUSTOMER"
    })
    token_res = await client.post("/api/v1/auth/token", data={"username": "cust_dispatch@roadsafe.com", "password": "Password123!"})
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Ticket
    ticket_payload = {
        "vehicle_type": "Sedan",
        "service_type": "TOW_TRUCK",
        "description": "Engine failure on highway",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "priority": "HIGH",
        "contact_phone": "+15550001111"
    }
    create_res = await client.post("/api/v1/tickets", json=ticket_payload, headers=headers)
    assert create_res.status_code == 201
    ticket_data = create_res.json()["ticket"]
    ticket_id = ticket_data["id"]

    # Initial Status after no matching responder -> NO_RESPONDER
    assert ticket_data["status"] in ["DISPATCHING", "NO_RESPONDER"]

    # Valid Status Transition Test: NO_RESPONDER -> REASSIGN
    reassign_res = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "REASSIGN", "reason": "Retrying dispatch"},
        headers=headers
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["status"] == "REASSIGN"

    # Invalid Transition Test: REASSIGN -> COMPLETED (Forbidden state jump)
    invalid_res = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "COMPLETED"},
        headers=headers
    )
    assert invalid_res.status_code == 400
    assert "Invalid status transition" in invalid_res.json()["detail"]