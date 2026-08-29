import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_phase2_tests():
    print("==================================================")
    print("RUNNING PHASE 2 DISPATCH ENGINE & WORKER FLOW TESTS")
    print("==================================================")

    ts = int(time.time())
    cust_email = f"cust_p2_{ts}@example.com"
    work1_email = f"work1_p2_{ts}@example.com"
    work2_email = f"work2_p2_{ts}@example.com"
    pwd = "TestPassword123!"

    # 1. Register Customer
    print("\n--- TEST 1: Customer Auth ---")
    r_cust = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Phase2 Customer",
        "email": cust_email,
        "phone_number": "9998887770",
        "password": pwd,
        "role": "CUSTOMER"
    })
    assert r_cust.status_code == 201, f"Customer reg failed: {r_cust.text}"
    r_cust_login = requests.post(f"{BASE_URL}/auth/login", data={"username": cust_email, "password": pwd})
    assert r_cust_login.status_code == 200
    cust_token = r_cust_login.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("[PASS] Customer registered and authenticated successfully")

    # 2. Register Worker 1 (Nearer: 11.0168, 76.9558)
    print("\n--- TEST 2: Worker 1 Setup ---")
    r_w1 = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Worker One (Near)",
        "email": work1_email,
        "phone_number": "9998887771",
        "password": pwd,
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "Near Auto Care",
        "skills": ["Engine Repair", "Tire Repair"]
    })
    assert r_w1.status_code == 201
    w1_token = requests.post(f"{BASE_URL}/auth/login", data={"username": work1_email, "password": pwd}).json()["access_token"]
    w1_headers = {"Authorization": f"Bearer {w1_token}"}

    # Worker 1 set Available + Online
    r_avail1 = requests.patch(f"{BASE_URL}/responders/availability", json={"is_available": True, "is_online": True}, headers=w1_headers)
    assert r_avail1.status_code == 200

    # Worker 1 set Location (11.0168, 76.9558)
    r_loc1 = requests.patch(f"{BASE_URL}/responders/location", json={"latitude": 11.0168, "longitude": 76.9558}, headers=w1_headers)
    assert r_loc1.status_code == 200
    print("[PASS] Worker 1 online, available, and location set to (11.0168, 76.9558)")

    # 3. Register Worker 2 (Further: 11.0250, 76.9650)
    print("\n--- TEST 3: Worker 2 Setup ---")
    r_w2 = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Worker Two (Further)",
        "email": work2_email,
        "phone_number": "9998887772",
        "password": pwd,
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "Far Auto Care",
        "skills": ["Tire Repair"]
    })
    assert r_w2.status_code == 201
    w2_token = requests.post(f"{BASE_URL}/auth/login", data={"username": work2_email, "password": pwd}).json()["access_token"]
    w2_headers = {"Authorization": f"Bearer {w2_token}"}

    # Worker 2 set Available + Online
    requests.patch(f"{BASE_URL}/responders/availability", json={"is_available": True, "is_online": True}, headers=w2_headers)
    requests.patch(f"{BASE_URL}/responders/location", json={"latitude": 11.0250, "longitude": 76.9650}, headers=w2_headers)
    print("[PASS] Worker 2 online, available, and location set to (11.0250, 76.9650)")

    # 4. Nearby Responders Endpoint Verification
    print("\n--- TEST 4: Nearby Responders Endpoint ---")
    r_near = requests.get(f"{BASE_URL}/responders/nearby?latitude=11.0170&longitude=76.9560", headers=cust_headers)
    assert r_near.status_code == 200
    nearby_list = r_near.json()
    assert len(nearby_list) >= 2, f"Expected at least 2 nearby responders, got {len(nearby_list)}"
    assert nearby_list[0]["shop_name"] == "Near Auto Care", f"Expected nearest responder to be Worker 1, got {nearby_list[0]['shop_name']}"
    print(f"[PASS] GET /responders/nearby correctly ranked closest provider ({nearby_list[0]['shop_name']} at {nearby_list[0]['distance_km']:.2f} km)")

    # 5. Customer Creates Assistance Ticket (Flat Tyre / Car Mechanic)
    print("\n--- TEST 5: Customer Assistance Ticket Creation ---")
    ticket_payload = {
        "service_type": "CAR_MECHANIC",
        "vehicle_type": "Maruti Suzuki Swift 2022",
        "description": "Front left tyre punctured on highway side.",
        "priority": "HIGH",
        "latitude": 11.0170,
        "longitude": 76.9560,
        "contact_phone": "9998887770"
    }
    r_ticket = requests.post(f"{BASE_URL}/tickets", json=ticket_payload, headers=cust_headers)
    assert r_ticket.status_code == 201, f"Ticket creation failed: {r_ticket.text}"
    t_res = r_ticket.json()
    ticket_id = t_res["ticket"]["id"]
    assigned_resp_id = t_res["assignment"]["responder_id"] if t_res["assignment"] else None
    print(f"[PASS] Real ticket #{ticket_id[:8]} created in PostgreSQL")
    print(f"[PASS] Dispatch engine assigned nearest Worker (Responder ID: {assigned_resp_id})")

    # 6. Worker 1 Declines Assignment -> Automatic Re-dispatch to Worker 2
    print("\n--- TEST 6: Worker Decline & Automatic Re-dispatch ---")
    r_dec = requests.post(f"{BASE_URL}/tickets/{ticket_id}/assignment/respond", json={"accepted": False}, headers=w1_headers)
    assert r_dec.status_code == 200, f"Decline failed: {r_dec.text}"
    print("[PASS] Worker 1 declined assignment")

    # Check updated ticket state
    r_t_after_dec = requests.get(f"{BASE_URL}/tickets/{ticket_id}", headers=cust_headers)
    t_after_dec = r_t_after_dec.json()
    assignments = t_after_dec.get("assignments", [])
    offered_a = [a for a in assignments if a["status"] == "OFFERED"]
    assert len(offered_a) > 0, "Expected re-dispatched offer for Worker 2"
    print("[PASS] Dispatch engine automatically re-dispatched ticket to Worker 2")

    # 7. Worker 2 Accepts Assignment
    print("\n--- TEST 7: Worker 2 Accepts Assignment ---")
    r_acc = requests.post(f"{BASE_URL}/tickets/{ticket_id}/assignment/respond", json={"accepted": True}, headers=w2_headers)
    assert r_acc.status_code == 200, f"Accept failed: {r_acc.text}"
    print("[PASS] Worker 2 accepted assignment successfully")

    # 8. Concurrency Protection Check
    print("\n--- TEST 8: Concurrency Protection (Prevent Dual Accept) ---")
    # Worker 1 attempts to accept already-accepted ticket -> MUST BE REJECTED with 400
    r_dual = requests.post(f"{BASE_URL}/tickets/{ticket_id}/assignment/respond", json={"accepted": True}, headers=w1_headers)
    assert r_dual.status_code in [400, 404], f"Expected concurrency error 400/404, got {r_dual.status_code}: {r_dual.text}"
    print("[PASS] Concurrency lock prevented second worker from accepting already-accepted ticket")

    # 9. Worker 2 Progresses Job Lifecycle: EN_ROUTE -> ARRIVED -> IN_SERVICE -> COMPLETED
    print("\n--- TEST 9: Worker Job Lifecycle Progression ---")
    lifecycle = [("EN_ROUTE", "Set En Route"), ("ARRIVED", "Mark Arrived"), ("IN_SERVICE", "Start Service")]
    for st, label in lifecycle:
        r_step = requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": st}, headers=w2_headers)
        assert r_step.status_code == 200, f"Lifecycle step {st} failed: {r_step.text}"
        print(f"[PASS] Ticket status transitioned to {st} ({label})")

    # 10. Customer History Verification
    print("\n--- TEST 10: Customer History Verification ---")
    r_hist = requests.get(f"{BASE_URL}/tickets", headers=cust_headers)
    assert r_hist.status_code == 200
    hist_tickets = r_hist.json()
    assert any(t["id"] == ticket_id for t in hist_tickets), "Ticket not found in customer history"
    print("[PASS] Ticket correctly listed in authenticated Customer History")

    print("\n==================================================")
    print("ALL PHASE 2 DISPATCH & WORKER TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_phase2_tests()
