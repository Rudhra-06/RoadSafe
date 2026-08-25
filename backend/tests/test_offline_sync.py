import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_offline_sync_idempotency(client: AsyncClient):
    # Register & Login Responder
    await client.post("/api/v1/auth/register", json={
        "email": "responder_sync@roadsafe.com",
        "password": "Password123!",
        "full_name": "Sync Responder",
        "role": "RESPONDER"
    })
    login_res = await client.post("/api/v1/auth/token", data={"username": "responder_sync@roadsafe.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Responder Profile
    await client.post("/api/v1/responders", json={"type": "TOW_TRUCK"}, headers=headers)

    sync_payload = {
        "actions": [
            {
                "idempotency_key": "unique-key-12345",
                "action_type": "LOCATION_UPDATE",
                "payload": {"latitude": 34.0522, "longitude": -118.2437},
                "client_timestamp": "2026-03-30T10:00:00Z"
            }
        ]
    }

    # First Sync Execution -> SUCCESS
    res1 = await client.post("/api/v1/offline/sync", json=sync_payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["processed_count"] == 1
    assert data1["results"][0]["status"] == "SUCCESS"

    # Retry Duplicate Execution -> DUPLICATE_SKIPPED
    res2 = await client.post("/api/v1/offline/sync", json=sync_payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["skipped_count"] == 1
    assert data2["results"][0]["status"] == "DUPLICATE_SKIPPED"