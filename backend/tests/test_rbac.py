import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rbac_access_control(client: AsyncClient):
    # 1. Register Customer & Admin
    await client.post("/api/v1/auth/register", json={
        "email": "user@roadsafe.com",
        "password": "Password123!",
        "full_name": "Standard User",
        "role": "CUSTOMER"
    })
    await client.post("/api/v1/auth/register", json={
        "email": "admin@roadsafe.com",
        "password": "Password123!",
        "full_name": "Admin User",
        "role": "ADMIN"
    })

    # Get Customer Token
    c_res = await client.post("/api/v1/auth/token", data={"username": "user@roadsafe.com", "password": "Password123!"})
    cust_token = c_res.json()["access_token"]

    # Get Admin Token
    a_res = await client.post("/api/v1/auth/token", data={"username": "admin@roadsafe.com", "password": "Password123!"})
    admin_token = a_res.json()["access_token"]

    # Customer tries Admin-only route GET /users -> 403 Forbidden
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    forbidden_res = await client.get("/api/v1/users", headers=cust_headers)
    assert forbidden_res.status_code == 403

    # Admin accesses GET /users -> 200 OK
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    ok_res = await client.get("/api/v1/users", headers=admin_headers)
    assert ok_res.status_code == 200