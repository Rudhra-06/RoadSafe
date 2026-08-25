import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    # Register Customer
    reg_payload = {
        "email": "customer@roadsafe.com",
        "password": "Password123!",
        "full_name": "John Customer",
        "phone": "+1234567890",
        "role": "CUSTOMER"
    }
    response = await client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "customer@roadsafe.com"
    assert "id" in data

    # Login
    login_payload = {
        "username": "customer@roadsafe.com",
        "password": "Password123!"
    }
    login_res = await client.post("/api/v1/auth/token", data=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"