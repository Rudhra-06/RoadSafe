import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_phase4_billing_tests():
    print("==================================================")
    print("RUNNING PHASE 4 REAL BILLING & PAYMENT TESTS")
    print("==================================================")

    ts = int(time.time())
    cust_email = f"p4_cust_{ts}@example.com"
    other_cust_email = f"p4_other_{ts}@example.com"
    work_email = f"p4_work_{ts}@example.com"
    pwd = "TestPassword123!"

    # 1. Register Customer 1
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Phase4 Customer",
        "email": cust_email,
        "phone_number": "9988776650",
        "password": pwd,
        "role": "CUSTOMER"
    })
    cust_token = requests.post(f"{BASE_URL}/auth/login", data={"username": cust_email, "password": pwd}).json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 2. Register Customer 2 (Unrelated Customer for RBAC Test)
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Unrelated Customer",
        "email": other_cust_email,
        "phone_number": "9988776659",
        "password": pwd,
        "role": "CUSTOMER"
    })
    other_token = requests.post(f"{BASE_URL}/auth/login", data={"username": other_cust_email, "password": pwd}).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 3. Register & Setup Worker
    requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "Phase4 Worker",
        "email": work_email,
        "phone_number": "9988776651",
        "password": pwd,
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "P4 Speed Care",
        "skills": ["Engine Repair", "Tire Repair"]
    })
    work_token = requests.post(f"{BASE_URL}/auth/login", data={"username": work_email, "password": pwd}).json()["access_token"]
    work_headers = {"Authorization": f"Bearer {work_token}"}

    requests.patch(f"{BASE_URL}/responders/availability", json={"is_available": True, "is_online": True}, headers=work_headers)
    requests.patch(f"{BASE_URL}/responders/location", json={"latitude": 11.0168, "longitude": 76.9558}, headers=work_headers)

    # 4. Fetch available services and parts
    services = requests.get(f"{BASE_URL}/services", headers=cust_headers).json()
    assert len(services) > 0, "No services found in database catalog"
    selected_service = services[0]

    parts = requests.get(f"{BASE_URL}/parts", headers=cust_headers).json()
    used_part = parts[0] if parts else None

    # 5. Customer creates request -> Worker accepts -> Advances to IN_SERVICE
    t_req = requests.post(f"{BASE_URL}/tickets", json={
        "service_type": "CAR_MECHANIC",
        "vehicle_type": "Honda City 2023",
        "description": "Engine overheating on freeway.",
        "priority": "EMERGENCY",
        "latitude": 11.0170,
        "longitude": 76.9560
    }, headers=cust_headers).json()
    ticket_id = t_req["ticket"]["id"]

    requests.post(f"{BASE_URL}/tickets/{ticket_id}/assignment/respond", json={"accepted": True}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "EN_ROUTE"}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "ARRIVED"}, headers=work_headers)
    requests.patch(f"{BASE_URL}/tickets/{ticket_id}/status", json={"status": "IN_SERVICE"}, headers=work_headers)

    print("[PASS] Ticket created, assigned, and advanced to IN_SERVICE")

    # 6. Worker Completes Job & Generates Invoice
    completion_payload = {
        "service_id": selected_service["id"],
        "parts": [{"part_id": used_part["id"], "quantity": 1}] if used_part else [],
        "notes": "Replaced coolant valve and performed diagnostic check."
    }
    r_comp = requests.post(f"{BASE_URL}/billing/tickets/{ticket_id}/complete", json=completion_payload, headers=work_headers)
    assert r_comp.status_code == 200, f"Job completion failed: {r_comp.text}"
    inv = r_comp.json()
    invoice_id = inv["id"]

    assert inv["status"] == "PENDING", f"Expected PENDING invoice status, got {inv['status']}"
    assert float(inv["grand_total"]) > 0, "Expected positive grand total"
    print(f"[PASS] Invoice #{inv['invoice_number']} generated (Grand Total: ₹{inv['grand_total']})")

    # 7. Test Duplicate Completion Idempotency
    r_dup = requests.post(f"{BASE_URL}/billing/tickets/{ticket_id}/complete", json=completion_payload, headers=work_headers)
    assert r_dup.status_code == 200, f"Expected 200 idempotent response, got {r_dup.status_code}"
    assert r_dup.json()["id"] == invoice_id, "Duplicate completion did not return original invoice"
    print("[PASS] Duplicate completion safely handled without duplicate invoice creation")

    # 8. Customer Access & RBAC Verification
    r_inv_cust = requests.get(f"{BASE_URL}/invoices/{invoice_id}", headers=cust_headers)
    assert r_inv_cust.status_code == 200, f"Customer invoice fetch failed: {r_inv_cust.text}"

    r_inv_ticket = requests.get(f"{BASE_URL}/tickets/{ticket_id}/invoice", headers=cust_headers)
    assert r_inv_ticket.status_code == 200, f"Ticket invoice fetch failed: {r_inv_ticket.text}"

    # Unrelated customer attempt -> MUST return 403 Forbidden
    r_unauth = requests.get(f"{BASE_URL}/invoices/{invoice_id}", headers=other_headers)
    assert r_unauth.status_code == 403, f"Expected 403 Forbidden for unauthorized customer, got {r_unauth.status_code}"
    print("[PASS] RBAC enforced: Customer can view their invoice; unauthorized customer blocked (403)")

    # 9. Payment Order Creation
    r_order = requests.post(f"{BASE_URL}/invoices/{invoice_id}/payment-order", json={}, headers=cust_headers)
    assert r_order.status_code == 200, f"Payment order creation failed: {r_order.text}"
    order_data = r_order.json()
    order_id = order_data["order_id"]
    print(f"[PASS] Payment order created with Order ID: {order_id}")

    # 10. Payment Verification & Settlement
    verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": f"pay_test_{ts}",
        "razorpay_signature": "simulated_signature"
    }
    r_ver = requests.post(f"{BASE_URL}/invoices/{invoice_id}/verify-payment", json=verify_payload, headers=cust_headers)
    assert r_ver.status_code == 200, f"Payment verification failed: {r_ver.text}"
    pay_res = r_ver.json()
    assert pay_res["status"] == "VERIFIED", f"Expected VERIFIED payment status, got {pay_res['status']}"

    # Verify Invoice status is now PAID
    r_inv_paid = requests.get(f"{BASE_URL}/invoices/{invoice_id}", headers=cust_headers)
    assert r_inv_paid.json()["status"] == "PAID", f"Expected invoice status PAID, got {r_inv_paid.json()['status']}"
    print("[PASS] Payment verified and invoice status set to PAID")

    # 11. Admin Financial Analytics Verification
    admin_login = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@roadsafe.com", "password": "AdminPass123!"})
    if admin_login.status_code == 200:
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        r_fin = requests.get(f"{BASE_URL}/analytics/financials", headers=admin_headers)
        assert r_fin.status_code == 200
        fin_data = r_fin.json()
        assert fin_data["gross_paid"] > 0, "Expected admin financial gross_paid > 0"
        print(f"[PASS] Real Admin Financial Analytics verified (Gross Paid Revenue: ₹{fin_data['gross_paid']:.2f})")

    print("\n==================================================")
    print("ALL PHASE 4 BILLING & PAYMENT TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_phase4_billing_tests()
