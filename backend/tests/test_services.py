import pytest
from httpx import AsyncClient
from decimal import Decimal

@pytest.mark.asyncio
async def test_create_service_success(client: AsyncClient, admin_token_headers: dict):
    payload = {
        "name": "Towing Service",
        "description": "Flatbed towing up to 15km",
        "category": "Towing",
        "base_price": "75.00"
    }
    response = await client.post("/api/v1/services", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Towing Service"
    assert data["base_price"] == "75.00"
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_reject_negative_service_price(client: AsyncClient, admin_token_headers: dict):
    payload = {"name": "Invalid Service", "base_price": "-10.00"}
    response = await client.post("/api/v1/services", json=payload, headers=admin_token_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_reject_empty_service_name(client: AsyncClient, admin_token_headers: dict):
    payload = {"name": "   ", "base_price": "50.00"}
    response = await client.post("/api/v1/services", json=payload, headers=admin_token_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_deactivate_service(client: AsyncClient, admin_token_headers: dict):
    create_res = await client.post("/api/v1/services", json={"name": "Battery Jump", "base_price": "30.00"}, headers=admin_token_headers)
    service_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/services/{service_id}", headers=admin_token_headers)
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False

@pytest.mark.asyncio
async def test_rbac_service_creation_restricted(client: AsyncClient, customer_token_headers: dict):
    payload = {"name": "Unauthorized Service", "base_price": "100.00"}
    response = await client.post("/api/v1/services", json=payload, headers=customer_token_headers)
    assert response.status_code == 403