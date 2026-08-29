import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.responder_location import ResponderLocation


@pytest.mark.asyncio
async def test_location_aware_dispatch_coimbatore_vs_chennai(client: AsyncClient):
    # Customer: Coimbatore (11.0168, 76.9558)
    # Worker 1: Chennai (13.0827, 80.2707) -> ~426 km away (outside 50km radius)
    # Worker 2: Coimbatore (11.0180, 76.9560) -> ~0.14 km away (inside 50km radius)
    
    # 1. Register and setup Coimbatore Customer
    await client.post("/api/v1/auth/register", json={
        "email": "cust_cbe@roadsafe.com",
        "password": "Password123!",
        "full_name": "Coimbatore Driver",
        "role": "CUSTOMER"
    })
    cust_token = (await client.post("/api/v1/auth/token", data={"username": "cust_cbe@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 2. Register Chennai Worker
    await client.post("/api/v1/auth/register", json={
        "email": "worker_chennai@roadsafe.com",
        "password": "Password123!",
        "full_name": "Chennai Mechanic",
        "role": "RESPONDER"
    })
    w1_token = (await client.post("/api/v1/auth/token", data={"username": "worker_chennai@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    w1_headers = {"Authorization": f"Bearer {w1_token}"}
    await client.patch("/api/v1/responders/availability", json={"is_available": True, "is_online": True}, headers=w1_headers)
    await client.patch("/api/v1/responders/location", json={"latitude": 13.0827, "longitude": 80.2707}, headers=w1_headers)

    # 3. Create ticket when only Chennai worker is available -> Should get NO_RESPONDER
    cbe_ticket_payload = {
        "vehicle_type": "Hatchback",
        "service_type": "CAR_MECHANIC",
        "description": "Flat tyre near Gandhipuram Coimbatore",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "priority": "MEDIUM",
        "contact_phone": "+919876543210"
    }
    t1_res = await client.post("/api/v1/tickets", json=cbe_ticket_payload, headers=cust_headers)
    assert t1_res.status_code == 201
    t1_data = t1_res.json()["ticket"]
    assert t1_data["status"] == "NO_RESPONDER"
    assert t1_res.json()["assignment"] is None

    # 4. Register Coimbatore Worker
    await client.post("/api/v1/auth/register", json={
        "email": "worker_cbe@roadsafe.com",
        "password": "Password123!",
        "full_name": "Coimbatore Mechanic",
        "role": "RESPONDER"
    })
    w2_token = (await client.post("/api/v1/auth/token", data={"username": "worker_cbe@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    w2_headers = {"Authorization": f"Bearer {w2_token}"}
    await client.patch("/api/v1/responders/availability", json={"is_available": True, "is_online": True}, headers=w2_headers)
    await client.patch("/api/v1/responders/location", json={"latitude": 11.0180, "longitude": 76.9560}, headers=w2_headers)

    # 5. Create new ticket in Coimbatore -> Should be ASSIGNED to Coimbatore worker
    t2_res = await client.post("/api/v1/tickets", json=cbe_ticket_payload, headers=cust_headers)
    assert t2_res.status_code == 201
    t2_data = t2_res.json()["ticket"]
    t2_assignment = t2_res.json()["assignment"]
    assert t2_data["status"] == "ASSIGNED"
    assert t2_assignment is not None

    w2_profile = (await client.get("/api/v1/responders/me", headers=w2_headers)).json()
    assert t2_assignment["responder_id"] == w2_profile["id"]


@pytest.mark.asyncio
async def test_stale_location_rejected(client: AsyncClient, db_session: AsyncSession):
    # Worker with stale location (>86400s) must be rejected
    await client.post("/api/v1/auth/register", json={
        "email": "worker_stale@roadsafe.com",
        "password": "Password123!",
        "full_name": "Stale Worker",
        "role": "RESPONDER"
    })
    w_token = (await client.post("/api/v1/auth/token", data={"username": "worker_stale@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    w_headers = {"Authorization": f"Bearer {w_token}"}
    await client.patch("/api/v1/responders/availability", json={"is_available": True, "is_online": True}, headers=w_headers)
    
    # Manually insert stale location 2 days ago
    w_profile = (await client.get("/api/v1/responders/me", headers=w_headers)).json()
    stale_loc = ResponderLocation(
        responder_id=w_profile["id"],
        latitude=11.0168,
        longitude=76.9558,
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db_session.add(stale_loc)
    await db_session.commit()

    cust_token = (await client.post("/api/v1/auth/token", data={"username": "cust_cbe@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    ticket_res = await client.post("/api/v1/tickets", json={
        "vehicle_type": "Sedan",
        "service_type": "CAR_MECHANIC",
        "description": "Engine breakdown near Stale worker",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "priority": "HIGH",
        "contact_phone": "+919876543210"
    }, headers=cust_headers)
    # The stale worker must not be assigned
    assignments = ticket_res.json()["ticket"]["assignments"]
    assigned_responders = [a["responder_id"] for a in assignments if a["status"] == "OFFERED"]
    assert w_profile["id"] not in assigned_responders


@pytest.mark.asyncio
async def test_invoice_flow_and_customer_rbac(client: AsyncClient, admin_token_headers: dict):
    # Create an active service as admin first
    svc_res = await client.post("/api/v1/services", json={
        "name": "General Mechanical Repair",
        "description": "General repairs and roadside fixes",
        "category": "Mechanical",
        "base_price": "150.00"
    }, headers=admin_token_headers)
    assert svc_res.status_code == 201
    service_id = svc_res.json()["id"]

    # Setup Customer A and Customer B
    await client.post("/api/v1/auth/register", json={
        "email": "cust_a@roadsafe.com",
        "password": "Password123!",
        "full_name": "Customer A",
        "role": "CUSTOMER"
    })
    token_a = (await client.post("/api/v1/auth/token", data={"username": "cust_a@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    await client.post("/api/v1/auth/register", json={
        "email": "cust_b@roadsafe.com",
        "password": "Password123!",
        "full_name": "Customer B",
        "role": "CUSTOMER"
    })
    token_b = (await client.post("/api/v1/auth/token", data={"username": "cust_b@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Worker
    await client.post("/api/v1/auth/register", json={
        "email": "worker_inv@roadsafe.com",
        "password": "Password123!",
        "full_name": "Invoice Worker",
        "role": "RESPONDER"
    })
    token_w = (await client.post("/api/v1/auth/token", data={"username": "worker_inv@roadsafe.com", "password": "Password123!"})).json()["access_token"]
    headers_w = {"Authorization": f"Bearer {token_w}"}
    await client.patch("/api/v1/responders/availability", json={"is_available": True, "is_online": True}, headers=headers_w)
    await client.patch("/api/v1/responders/location", json={"latitude": 11.0168, "longitude": 76.9558}, headers=headers_w)

    # Customer A creates ticket
    t_res = await client.post("/api/v1/tickets", json={
        "vehicle_type": "SUV",
        "service_type": "CAR_MECHANIC",
        "description": "Brake pad replacement",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "priority": "HIGH",
        "contact_phone": "+919876543210"
    }, headers=headers_a)
    ticket_id = t_res.json()["ticket"]["id"]

    # Worker accepts and moves ticket through lifecycle
    await client.post(f"/api/v1/tickets/{ticket_id}/assignment/respond", json={"accepted": True}, headers=headers_w)
    await client.patch(f"/api/v1/tickets/{ticket_id}/status", json={"status": "EN_ROUTE"}, headers=headers_w)
    await client.patch(f"/api/v1/tickets/{ticket_id}/status", json={"status": "ARRIVED"}, headers=headers_w)
    await client.patch(f"/api/v1/tickets/{ticket_id}/status", json={"status": "IN_SERVICE"}, headers=headers_w)

    # Worker completes job and generates invoice
    comp_res = await client.post(f"/api/v1/billing/tickets/{ticket_id}/complete", json={
        "service_id": service_id,
        "parts": [],
        "notes": "Replaced pads successfully"
    }, headers=headers_w)
    assert comp_res.status_code == 200
    invoice_data = comp_res.json()
    invoice_id = invoice_data["id"]
    assert invoice_data["ticket_id"] == ticket_id
    assert invoice_data["status"] == "PENDING"
    assert len(invoice_data["lines"]) >= 1

    # Customer A retrieves invoice by Invoice ID
    inv_res = await client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=headers_a)
    assert inv_res.status_code == 200
    assert inv_res.json()["id"] == invoice_id
    assert inv_res.json()["ticket_id"] == ticket_id

    # Customer A retrieves invoice by Ticket ID
    inv_t_res = await client.get(f"/api/v1/billing/invoices/{ticket_id}", headers=headers_a)
    assert inv_t_res.status_code == 200
    assert inv_t_res.json()["id"] == invoice_id

    # Customer A retrieves invoice via /tickets/{ticket_id}/invoice
    inv_t2_res = await client.get(f"/api/v1/tickets/{ticket_id}/invoice", headers=headers_a)
    assert inv_t2_res.status_code == 200
    assert inv_t2_res.json()["id"] == invoice_id

    # RBAC Test: Customer B tries to retrieve Customer A's invoice -> Must be 403 FORBIDDEN
    unauth_res = await client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=headers_b)
    assert unauth_res.status_code == 403
    assert "access denied" in unauth_res.json()["detail"].lower()

    # Customer A creates payment order
    order_res = await client.post(f"/api/v1/billing/invoices/{invoice_id}/payment-order", headers=headers_a)
    assert order_res.status_code == 200
    order_data = order_res.json()
    assert order_data["invoice_id"] == invoice_id
    assert "order_id" in order_data

    # Customer A verifies dev payment
    verify_res = await client.post(f"/api/v1/billing/invoices/{invoice_id}/verify-payment", json={
        "razorpay_order_id": order_data["order_id"],
        "razorpay_payment_id": "pay_dev_test123",
        "razorpay_signature": "sig_dev"
    }, headers=headers_a)
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "VERIFIED"

    # Verify invoice status is now PAID
    paid_inv = (await client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=headers_a)).json()
    assert paid_inv["status"] == "PAID"
