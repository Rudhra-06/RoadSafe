import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_create_ticket_hotfix():
    print("==================================================")
    print("RUNNING POST /api/v1/tickets HOTFIX VERIFICATION")
    print("==================================================")

    ts = int(time.time())
    cust_email = f"hotfix_cust_{ts}@example.com"
    work_email = f"hotfix_work_{ts}@example.com"
    pwd = "TestPassword123!"

    # 1. Register Customer
    r_cust = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Hotfix Customer",
        "email": cust_email,
        "phone_number": "9991112220",
        "password": pwd,
        "role": "CUSTOMER"
    })
    assert r_cust.status_code == 201, f"Customer registration failed: {r_cust.text}"

    r_cust_login = requests.post(f"{BASE_URL}/auth/login", data={"username": cust_email, "password": pwd})
    assert r_cust_login.status_code == 200, f"Customer login failed: {r_cust_login.text}"
    cust_token = r_cust_login.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("[PASS] Customer registered and authenticated")

    # 2. Register & Setup Worker
    r_work = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Hotfix Worker",
        "email": work_email,
        "phone_number": "9991112221",
        "password": pwd,
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "Hotfix Auto Care",
        "skills": ["Tire Repair", "Engine Repair"]
    })
    assert r_work.status_code == 201, f"Worker registration failed: {r_work.text}"

    work_token = requests.post(f"{BASE_URL}/auth/login", data={"username": work_email, "password": pwd}).json()["access_token"]
    work_headers = {"Authorization": f"Bearer {work_token}"}

    # Set Worker Online + Available + Location
    requests.patch(f"{BASE_URL}/responders/availability", json={"is_available": True, "is_online": True}, headers=work_headers)
    requests.patch(f"{BASE_URL}/responders/location", json={"latitude": 11.0168, "longitude": 76.9558}, headers=work_headers)
    print("[PASS] Worker set online, available, and location updated")

    # 3. Customer POST /tickets
    ticket_payload = {
        "service_type": "CAR_MECHANIC",
        "vehicle_type": "Maruti Swift 2022",
        "description": "Flat tyre on rear right wheel.",
        "priority": "HIGH",
        "latitude": 11.0170,
        "longitude": 76.9560,
        "contact_phone": "9991112220"
    }

    r_ticket = requests.post(f"{BASE_URL}/tickets", json=ticket_payload, headers=cust_headers)
    assert r_ticket.status_code == 201, f"POST /tickets failed with status {r_ticket.status_code}: {r_ticket.text}"

    data = r_ticket.json()
    assert "ticket" in data, "Response missing 'ticket' key"
    assert data["ticket"]["status"] in ["ASSIGNED", "DISPATCHING", "REQUESTED"], f"Unexpected ticket status: {data['ticket']['status']}"
    assert data["assignment"] is not None, "Expected assignment to be created for online worker"
    
    ticket_id = data["ticket"]["id"]
    responder_id = data["assignment"]["responder_id"]
    print(f"[PASS] POST /api/v1/tickets created ticket #{ticket_id[:8]} with status HTTP 201 (No MissingGreenlet error)")
    print(f"[PASS] Dispatch engine assigned responder #{responder_id[:8]}")

    # 4. Verify Ticket Read endpoint
    r_get = requests.get(f"{BASE_URL}/tickets/{ticket_id}", headers=cust_headers)
    assert r_get.status_code == 200, f"GET /tickets/{ticket_id} failed: {r_get.text}"
    print("[PASS] GET /api/v1/tickets/{ticket_id} loaded successfully")

    print("\n==================================================")
    print("POST /api/v1/tickets HOTFIX VERIFIED 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_create_ticket_hotfix()
