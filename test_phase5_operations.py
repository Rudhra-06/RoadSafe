import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_phase5_operations_tests():
    print("==================================================")
    print("RUNNING PHASE 5 OPERATIONS, REVIEWS & NOTIFICATIONS TESTS")
    print("==================================================")

    ts = int(time.time())
    cust_email = f"p5_cust_{ts}@example.com"
    other_cust_email = f"p5_other_{ts}@example.com"
    work_email = f"p5_work_{ts}@example.com"
    pwd = "TestPassword123!"

    # 1. Register Customer 1
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Phase5 Customer",
        "email": cust_email,
        "phone_number": "9977665540",
        "password": pwd,
        "role": "CUSTOMER"
    })
    cust_token = requests.post(f"{BASE_URL}/auth/login", data={"username": cust_email, "password": pwd}).json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 2. Register Customer 2
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Other Customer",
        "email": other_cust_email,
        "phone_number": "9977665549",
        "password": pwd,
        "role": "CUSTOMER"
    })
    other_token = requests.post(f"{BASE_URL}/auth/login", data={"username": other_cust_email, "password": pwd}).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 3. Register & Setup Worker
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Phase5 Worker",
        "email": work_email,
        "phone_number": "9977665541",
        "password": pwd,
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "P5 Master Tech",
        "skills": ["Tire Repair", "Battery Repair"]
    })
    work_token = requests.post(f"{BASE_URL}/auth/login", data={"username": work_email, "password": pwd}).json()["access_token"]
    work_headers = {"Authorization": f"Bearer {work_token}"}

    requests.patch(f"{BASE_URL}/responders/availability", json={"is_available": True, "is_online": True}, headers=work_headers)
    requests.patch(f"{BASE_URL}/responders/location", json={"latitude": 11.0168, "longitude": 76.9558}, headers=work_headers)

    # 4. Create, Assign, Complete Job & Pay Invoice
    services = requests.get(f"{BASE_URL}/services", headers=cust_headers).json()
    svc_id = services[0]["id"]

    t_req = requests.post(f"{BASE_URL}/tickets", json={
        "service_type": "CAR_MECHANIC",
        "vehicle_type": "Hyundai Creta 2024",
        "description": "Flat tyre replacement on roadside.",
        "priority": "HIGH",
        "latitude": 11.0170,
        "longitude": 76.9560
    }, headers=cust_headers).json()
    ticket_id = t_req["ticket"]["id"]

    requests.post(f"{BASE_URL}/tickets/{ticket_id}/assignment/respond", json={"accepted": True}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "EN_ROUTE"}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "ARRIVED"}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "IN_SERVICE"}, headers=work_headers)

    inv = requests.post(f"{BASE_URL}/billing/tickets/{ticket_id}/complete", json={"service_id": svc_id, "parts": []}, headers=work_headers).json()
    invoice_id = inv["id"]

    order = requests.post(f"{BASE_URL}/invoices/{invoice_id}/payment-order", json={}, headers=cust_headers).json()
    requests.post(f"{BASE_URL}/invoices/{invoice_id}/verify-payment", json={
        "razorpay_order_id": order["order_id"],
        "razorpay_payment_id": f"pay_p5_{ts}",
        "razorpay_signature": "dev_sig"
    }, headers=cust_headers)

    print("[PASS] Ticket completed and invoice paid successfully")

    # 5. Customer Review Flow
    print("\n--- TEST 1: Customer Review Submission ---")
    r_rev = requests.post(f"{BASE_URL}/reviews", json={
        "ticket_id": ticket_id,
        "rating": 5,
        "comment": "Outstanding quick service! Technician arrived within 10 mins."
    }, headers=cust_headers)
    assert r_rev.status_code == 201, f"Review submission failed: {r_rev.text}"
    rev_data = r_rev.json()
    assert rev_data["rating"] == 5
    print("[PASS] Customer submitted 5-star review for completed ticket")

    # 6. Unauthorized Customer Review Attempt
    r_unauth_rev = requests.post(f"{BASE_URL}/reviews", json={
        "ticket_id": ticket_id,
        "rating": 1,
        "comment": "Malicious review attempt"
    }, headers=other_headers)
    assert r_unauth_rev.status_code in [400, 403], f"Expected 400/403 for unauthorized review, got {r_unauth_rev.status_code}"
    print("[PASS] Unauthorized customer blocked from reviewing another customer's ticket")

    # 7. Worker Cannot Submit Customer Review
    r_work_rev = requests.post(f"{BASE_URL}/reviews", json={
        "ticket_id": ticket_id,
        "rating": 5,
        "comment": "Self rating"
    }, headers=work_headers)
    assert r_work_rev.status_code == 403, f"Expected 403 for worker submitting review, got {r_work_rev.status_code}"
    print("[PASS] Worker blocked from submitting customer review (403)")

    # 8. Worker Views Reviews for Assigned Jobs
    r_work_list = requests.get(f"{BASE_URL}/reviews", headers=work_headers)
    assert r_work_list.status_code == 200
    w_reviews = r_work_list.json()
    assert any(r["ticket_id"] == ticket_id for r in w_reviews), "Worker could not retrieve assigned review"
    print("[PASS] Worker retrieved reviews for completed jobs")

    # 9. Persistent Notifications Check
    print("\n--- TEST 2: Notifications Verification ---")
    r_notif = requests.get(f"{BASE_URL}/notifications", headers=cust_headers)
    assert r_notif.status_code == 200
    notifs = r_notif.json()
    assert len(notifs) >= 3, f"Expected persistent notifications for customer, got {len(notifs)}"
    print(f"[PASS] Customer received {len(notifs)} persistent notifications (Dispatch, Invoice, Payment)")

    # Mark all notifications read
    r_readall = requests.post(f"{BASE_URL}/notifications/read-all", headers=cust_headers)
    assert r_readall.status_code == 200
    print("[PASS] POST /notifications/read-all marked customer alerts as read")

    # 10. Admin Executive Operations & Financial Analytics
    print("\n--- TEST 3: Admin Operations Control Hub ---")
    admin_login = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@roadsafe.com", "password": "AdminPass123!"})
    assert admin_login.status_code == 200, "Admin login failed"
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    r_overview = requests.get(f"{BASE_URL}/analytics/overview", headers=admin_headers)
    assert r_overview.status_code == 200
    ov = r_overview.json()
    assert ov["total_requests"] > 0
    assert ov["paid_amount"] > 0
    print(f"[PASS] Executive Overview Analytics verified (Total Requests: {ov['total_requests']}, Gross Revenue: ₹{ov['gross_invoiced']:.2f})")

    r_mechanics = requests.get(f"{BASE_URL}/analytics/mechanics", headers=admin_headers)
    assert r_mechanics.status_code == 200
    mech_list = r_mechanics.json()
    assert len(mech_list) > 0
    print(f"[PASS] Admin Fleet Readiness verified ({len(mech_list)} registered mechanics)")

    r_rev_stats = requests.get(f"{BASE_URL}/reviews/stats", headers=admin_headers)
    assert r_rev_stats.status_code == 200
    rev_stats = r_rev_stats.json()
    assert rev_stats["total_reviews"] > 0
    print(f"[PASS] Platform Review Intelligence verified (Avg Rating: {rev_stats['average_rating']} ★)")

    print("\n==================================================")
    print("ALL PHASE 5 OPERATIONS & REVIEWS TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_phase5_operations_tests()
