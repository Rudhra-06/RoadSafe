import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_part_success(client: AsyncClient, admin_token_headers: dict):
    payload = {
        "name": "Synthetic Engine Oil 5W-30",
        "part_number": "OIL-5W30-01",
        "description": "1 Litre Can",
        "unit_price": "15.50",
        "stock_quantity": 40
    }
    response = await client.post("/api/v1/parts", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Synthetic Engine Oil 5W-30"
    assert data["stock_quantity"] == 40

@pytest.mark.asyncio
async def test_reject_negative_part_price_and_stock(client: AsyncClient, admin_token_headers: dict):
    payload_price = {"name": "Spark Plug", "unit_price": "-5.00", "stock_quantity": 10}
    res1 = await client.post("/api/v1/parts", json=payload_price, headers=admin_token_headers)
    assert res1.status_code == 422

    payload_stock = {"name": "Spark Plug", "unit_price": "5.00", "stock_quantity": -2}
    res2 = await client.post("/api/v1/parts", json=payload_stock, headers=admin_token_headers)
    assert res2.status_code == 422

@pytest.mark.asyncio
async def test_deactivate_part(client: AsyncClient, admin_token_headers: dict):
    create_res = await client.post("/api/v1/parts", json={"name": "Fuse 15A", "unit_price": "1.50", "stock_quantity": 100}, headers=admin_token_headers)
    part_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/parts/{part_id}", headers=admin_token_headers)
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False

@pytest.mark.asyncio
async def test_rbac_part_creation_restricted(client: AsyncClient, customer_token_headers: dict):
    payload = {"name": "Unauthorized Part", "unit_price": "10.00", "stock_quantity": 5}
    response = await client.post("/api/v1/parts", json=payload, headers=customer_token_headers)
    assert response.status_code == 403