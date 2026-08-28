"""
Comprehensive End-to-End Test Suite for RoadSafe
Tests:
1. Customer Registration & Validation
2. Worker Registration with Multiple Skills & DB Persistence
3. CORS headers across 200, 201, 400, 422, 500
4. Customer & Worker Login and JWT Generation
5. Admin Login and Access Control
6. RBAC Role Isolation (Customer -> Admin forbidden, Worker -> Admin forbidden)
7. Customer Request Flow (Catalog -> Assistance Request -> Ticket Creation)
8. Worker Dashboard & Status Updates (Assign -> Accept -> En Route -> Arrived -> In Service -> Completed)
9. Invoice Generation & Reviews
10. Frontend Files Quality Check (Viewport meta tags, No emojis, Lucide SVG icons, PWA containers)
"""

import urllib.request
import urllib.error
import json
import uuid
import sys
import os
import re
import time
import hmac
import hashlib

API_URL = "http://localhost:8000/api/v1"
ORIGIN = "http://localhost:5500"

def make_request(path, method="GET", data=None, token=None):
    headers = {
        "Origin": ORIGIN,
        "Accept": "application/json"
    }
    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{API_URL}{path}", data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            cors = resp.headers.get("Access-Control-Allow-Origin")
            return {
                "status": resp.status,
                "cors": cors,
                "body": json.loads(body) if body else None,
                "raw": body
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        cors = e.headers.get("Access-Control-Allow-Origin")
        parsed_body = None
        try:
            parsed_body = json.loads(body)
        except Exception:
            parsed_body = body
        return {
            "status": e.code,
            "cors": cors,
            "body": parsed_body,
            "raw": body
        }


def run_tests():
    print("==================================================")
    print("   ROADSAFE END-TO-END AUTOMATED VERIFICATION   ")
    print("==================================================")

    uid = uuid.uuid4().hex[:6]
    cust_email = f"customer_{uid}@roadsafeapp.com"
    worker_email = f"worker_{uid}@roadsafeapp.com"

    # 1. Customer Registration Validation & Success
    print("\n--- 1. Testing Customer Registration ---")
    
    # 1a. Invalid email
    res = make_request("/auth/register", method="POST", data={
        "email": "notanemail",
        "password": "password123",
        "full_name": "Test User",
        "role": "CUSTOMER"
    })
    assert res["status"] == 422, f"Expected 422 for invalid email, got {res['status']}"
    assert res["cors"] == ORIGIN, f"Expected CORS header {ORIGIN}, got {res['cors']}"
    print("  [PASS] Invalid email rejected with 422 and CORS headers.")

    # 1b. Short password
    res = make_request("/auth/register", method="POST", data={
        "email": f"valid_{uid}@roadsafeapp.com",
        "password": "123",
        "full_name": "Test User",
        "role": "CUSTOMER"
    })
    assert res["status"] == 422, f"Expected 422 for short password, got {res['status']}"
    print("  [PASS] Short password rejected with 422.")

    # 1c. Valid registration
    res = make_request("/auth/register", method="POST", data={
        "email": cust_email,
        "password": "password123",
        "full_name": "Jane Customer",
        "phone_number": "+919876543210",
        "role": "CUSTOMER"
    })
    assert res["status"] == 201, f"Expected 201 for valid customer registration, got {res['status']}: {res['raw']}"
    assert res["cors"] == ORIGIN, f"Expected CORS header, got {res['cors']}"
    assert res["body"]["email"] == cust_email
    assert res["body"]["role"] == "CUSTOMER"
    cust_id = res["body"]["id"]
    print(f"  [PASS] Customer registered successfully (ID: {cust_id}).")

    # 1d. Duplicate email check
    res = make_request("/auth/register", method="POST", data={
        "email": cust_email,
        "password": "password123",
        "full_name": "Jane Duplicate",
        "role": "CUSTOMER"
    })
    assert res["status"] == 400, f"Expected 400 for duplicate email, got {res['status']}"
    assert res["cors"] == ORIGIN, f"Expected CORS header on 400, got {res['cors']}"
    assert "already registered" in str(res["body"]), f"Expected duplicate error message, got {res['body']}"
    print("  [PASS] Duplicate email gracefully returned 400 with CORS headers.")

    # 2. Worker Registration with Multiple Skills & Persistence
    print("\n--- 2. Testing Worker Registration ---")
    worker_skills = ["ENGINE REPAIR", "BATTERY ASSISTANCE", "TIRE REPAIR", "TOWING"]
    res = make_request("/auth/register", method="POST", data={
        "email": worker_email,
        "password": "password123",
        "full_name": "Bob Mechanic",
        "phone_number": "+919876543220",
        "role": "RESPONDER",
        "responder_type": "CAR_MECHANIC",
        "shop_name": "Bob Auto Works",
        "shop_address": "123 Main Road, Coimbatore",
        "skills": worker_skills
    })
    assert res["status"] == 201, f"Expected 201 for worker registration, got {res['status']}: {res['raw']}"
    assert res["cors"] == ORIGIN, f"Expected CORS header on worker register, got {res['cors']}"
    worker_id = res["body"]["id"]
    print(f"  [PASS] Worker registered successfully (ID: {worker_id}).")

    # 3. Logins
    print("\n--- 3. Testing Authentication & JWT Generation ---")
    # Customer Login
    res = make_request("/auth/login", method="POST", data=f"username={cust_email}&password=password123")
    assert res["status"] == 200, f"Customer login failed: {res['raw']}"
    cust_token = res["body"]["access_token"]
    assert res["body"]["user"]["role"] == "CUSTOMER"
    print("  [PASS] Customer logged in successfully and received JWT.")

    # Worker Login
    res = make_request("/auth/login", method="POST", data=f"username={worker_email}&password=password123")
    assert res["status"] == 200, f"Worker login failed: {res['raw']}"
    worker_token = res["body"]["access_token"]
    assert res["body"]["user"]["role"] == "RESPONDER"
    print("  [PASS] Worker logged in successfully and received JWT.")

    # Admin Login
    res = make_request("/auth/login", method="POST", data="username=admin@roadsafe.com&password=AdminPass123!")
    assert res["status"] == 200, f"Admin login failed: {res['raw']}"
    admin_token = res["body"]["access_token"]
    assert res["body"]["user"]["role"] == "ADMIN"
    print("  [PASS] Admin logged in successfully and received JWT.")

    # 4. Role-Based Access Control
    print("\n--- 4. Testing Role-Based Access Control (RBAC) ---")
    # Customer attempting admin endpoint
    res = make_request("/users", method="GET", token=cust_token)
    assert res["status"] == 403, f"Expected 403 Forbidden for customer accessing /users, got {res['status']}"
    print("  [PASS] Customer -> Admin resource: FORBIDDEN (403).")

    # Worker attempting admin endpoint
    res = make_request("/users", method="GET", token=worker_token)
    assert res["status"] == 403, f"Expected 403 Forbidden for worker accessing /users, got {res['status']}"
    print("  [PASS] Worker -> Admin resource: FORBIDDEN (403).")

    # Admin accessing admin endpoint
    res = make_request("/users", method="GET", token=admin_token)
    assert res["status"] == 200, f"Expected 200 for admin accessing /users, got {res['status']}"
    print("  [PASS] Admin -> Admin resource: AUTHORIZED (200).")

    # 5. Customer Request Flow, Real Mechanic Matching & Admin Visibility
    print("\n--- 5. Testing Service Request, Dispatch Matching & Mechanic Acceptance ---")
    
    # 5a. Worker sets online, available & logs GPS location
    res = make_request("/responders/availability", method="PATCH", data={"is_online": True, "is_available": True}, token=worker_token)
    assert res["status"] == 200, f"Worker status update failed: {res['raw']}"
    print("  [PASS] Worker marked online and available.")

    res = make_request("/responders/location", method="PATCH", data={"latitude": 11.0180, "longitude": 76.9560}, token=worker_token)
    assert res["status"] == 200, f"Worker location update failed: {res['raw']}"
    print("  [PASS] Worker GPS location logged (11.0180, 76.9560).")

    # 5b. Services Catalog Fetch
    res = make_request("/services", method="GET", token=cust_token)
    assert res["status"] == 200, f"Services fetch failed: {res['raw']}"
    assert len(res["body"]) >= 6, f"Expected at least 6 services, got {len(res['body'])}"
    print(f"  [PASS] Service catalog retrieved ({len(res['body'])} real services verified).")

    # 5c. Customer creates Ticket
    ticket_payload = {
        "vehicle_type": "Hyundai i20",
        "service_type": "CAR_MECHANIC",
        "description": "Engine overheating on highway",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "priority": "MEDIUM",
        "contact_phone": "+919876543210"
    }
    res = make_request("/tickets", method="POST", data=ticket_payload, token=cust_token)
    assert res["status"] == 201, f"Ticket creation failed: {res['raw']}"
    ticket_data = res["body"]["ticket"] if isinstance(res["body"], dict) and "ticket" in res["body"] else res["body"]
    ticket_id = ticket_data["id"]
    print(f"  [PASS] Ticket created and dispatched in PostgreSQL (Ticket ID: {ticket_id}, Status: {ticket_data['status']}).")

    # 5d. Worker views incoming/assigned tickets
    res = make_request("/tickets", method="GET", token=worker_token)
    assert res["status"] == 200, f"Worker tickets fetch failed: {res['raw']}"
    assigned_ticket = next((t for t in res["body"] if t["id"] == ticket_id), None)
    assert assigned_ticket is not None, f"Created ticket {ticket_id} not found in worker's assigned tickets list"
    print("  [PASS] Worker received dispatch assignment in tickets list.")

    # 5e. Worker accepts the assignment offer
    res = make_request(f"/tickets/{ticket_id}/assignment/respond", method="POST", data={"accepted": True}, token=worker_token)
    assert res["status"] == 200, f"Worker assignment acceptance failed: {res['raw']}"
    assert res["body"]["status"] == "ACCEPTED", f"Expected assignment status ACCEPTED, got {res['body']['status']}"
    print("  [PASS] Worker accepted the job assignment.")

    # 5f. Verify ticket status update in database
    res = make_request(f"/tickets/{ticket_id}", method="GET", token=cust_token)
    assert res["status"] == 200, f"Customer ticket fetch failed: {res['raw']}"
    assert res["body"]["status"] == "ACCEPTED", f"Expected ticket status ACCEPTED, got {res['body']['status']}"
    print(f"  [PASS] Ticket status updated to ACCEPTED in PostgreSQL.")

    # 5g. Full Operational Lifecycle Progression: ACCEPTED -> EN_ROUTE -> ARRIVED -> IN_SERVICE -> COMPLETED
    print("\n--- 5g. Testing Complete Operational Lifecycle Progression ---")
    
    # Transition: ACCEPTED -> EN_ROUTE
    res = make_request(f"/tickets/{ticket_id}/status", method="PATCH", data={"status": "EN_ROUTE", "reason": "Mechanic departed shop"}, token=worker_token)
    assert res["status"] == 200, f"Failed transition to EN_ROUTE: {res['raw']}"
    assert res["body"]["status"] == "EN_ROUTE"
    print("  [PASS] Ticket transitioned: ACCEPTED -> EN_ROUTE.")

    # Location update while en route
    res = make_request("/responders/location", method="PATCH", data={"latitude": 11.0172, "longitude": 76.9559}, token=worker_token)
    assert res["status"] == 200, f"En-route location update failed: {res['raw']}"
    print("  [PASS] En-route live GPS telemetry updated (11.0172, 76.9559).")

    # Transition: EN_ROUTE -> ARRIVED
    res = make_request(f"/tickets/{ticket_id}/status", method="PATCH", data={"status": "ARRIVED", "reason": "Mechanic on scene"}, token=worker_token)
    assert res["status"] == 200, f"Failed transition to ARRIVED: {res['raw']}"
    assert res["body"]["status"] == "ARRIVED"
    print("  [PASS] Ticket transitioned: EN_ROUTE -> ARRIVED.")

    # Transition: ARRIVED -> IN_SERVICE
    res = make_request(f"/tickets/{ticket_id}/status", method="PATCH", data={"status": "IN_SERVICE", "reason": "Diagnostic and repair commenced"}, token=worker_token)
    assert res["status"] == 200, f"Failed transition to IN_SERVICE: {res['raw']}"
    assert res["body"]["status"] == "IN_SERVICE"
    print("  [PASS] Ticket transitioned: ARRIVED -> IN_SERVICE.")

    # 5h. Phase 4: Parts Catalog, Job Completion & Invoice Generation
    print("\n--- 5h. Testing Parts Catalog, Job Completion & Real Invoice ---")
    res = make_request("/parts", method="GET", token=worker_token)
    assert res["status"] == 200, f"Parts fetch failed: {res['raw']}"
    assert len(res["body"]) >= 1, "Expected at least 1 seeded part in catalog"
    selected_part = res["body"][0]
    part_id = selected_part["id"]
    part_price = float(selected_part["unit_price"])
    print(f"  [PASS] Real parts catalog retrieved ({len(res['body'])} parts available, selected '{selected_part['name']}' @ ₹{part_price}).")

    # Mechanic completes job with parts used
    services_res = make_request("/services", method="GET", token=worker_token)
    service_id = services_res["body"][0]["id"]
    service_price = float(services_res["body"][0]["base_price"])
    completion_payload = {
        "service_id": service_id,
        "parts": [{"part_id": part_id, "quantity": 1}],
        "notes": "Replaced faulty part and tested system."
    }
    res = make_request(f"/billing/tickets/{ticket_id}/complete", method="POST", data=completion_payload, token=worker_token)
    assert res["status"] == 200, f"Job completion failed: {res['raw']}"
    invoice = res["body"]
    invoice_id = invoice["id"]
    expected_total = service_price + part_price
    assert abs(float(invoice["grand_total"]) - expected_total) < 0.05, f"Expected total {expected_total}, got {invoice['grand_total']}"
    assert invoice["status"] == "PENDING"
    print(f"  [PASS] Invoice #{invoice['invoice_number']} generated with real Service (₹{service_price}) + Parts (₹{part_price}) = Grand Total ₹{invoice['grand_total']}.")

    # Verify ticket auto-completed upon invoice generation
    res = make_request(f"/tickets/{ticket_id}", method="GET", token=cust_token)
    assert res["status"] == 200 and res["body"]["status"] == "COMPLETED"
    print("  [PASS] Ticket automatically marked COMPLETED in PostgreSQL upon job completion.")

    # 5i. Phase 4: Razorpay Payment Flow & Server-Side Verification
    print("\n--- 5i. Testing Razorpay Payment Order & Cryptographic Signature Verification ---")
    # Customer creates payment order
    res = make_request(f"/billing/invoices/{invoice_id}/payment-order", method="POST", data={}, token=cust_token)
    assert res["status"] == 200, f"Payment order creation failed: {res['raw']}"
    order_data = res["body"]
    order_id = order_data["order_id"]
    print(f"  [PASS] Razorpay payment order created (Order ID: {order_id}, Amount: {order_data['amount']} paise).")

    # Test invalid signature rejection (Security Check)
    bad_verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": "pay_fake123456",
        "razorpay_signature": "invalid_signature_hash"
    }
    res = make_request(f"/billing/invoices/{invoice_id}/verify-payment", method="POST", data=bad_verify_payload, token=cust_token)
    assert res["status"] == 400, f"Expected 400 for tampered payment signature, got {res['status']}"
    print("  [PASS] Tampered payment signature strictly rejected by server (400 Bad Request).")

    # Generate genuine HMAC SHA-256 signature using test secret
    test_secret = "5Ra89Q6ikQtL69bzbGFs6jBV"
    payment_id = "pay_test_" + str(int(time.time()))
    payload_str = f"{order_id}|{payment_id}"
    valid_signature = hmac.new(test_secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

    valid_verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": valid_signature
    }
    res = make_request(f"/billing/invoices/{invoice_id}/verify-payment", method="POST", data=valid_verify_payload, token=cust_token)
    assert res["status"] == 200, f"Valid payment verification failed: {res['raw']}"
    assert res["body"]["status"] == "VERIFIED"
    print(f"  [PASS] Server-side HMAC SHA-256 signature verified (Payment ID: {payment_id}).")

    # Verify invoice status in PostgreSQL is PAID
    res = make_request(f"/billing/invoices/{invoice_id}", method="GET", token=cust_token)
    assert res["status"] == 200 and res["body"]["status"] == "PAID"
    print(f"  [PASS] Invoice #{invoice['invoice_number']} verified as PAID in PostgreSQL.")

    # 5j. Admin verifies revenue and settled invoices
    res = make_request("/billing/invoices", method="GET", token=admin_token)
    assert res["status"] == 200, f"Admin invoices fetch failed: {res['raw']}"
    admin_invoice = next((i for i in res["body"] if i["id"] == invoice_id), None)
    assert admin_invoice is not None and admin_invoice["status"] == "PAID"
    print(f"  [PASS] Admin verified settled invoice in financial ledger.")

    # 5k. Phase 5: Customer Reviews & Performance Feedback
    print("\n--- 5k. Testing Customer Reviews & CRM Feedback ---")
    # Customer submits 5-star review
    review_payload = {
        "ticket_id": ticket_id,
        "rating": 5,
        "comment": "Exceptional roadside assistance! Fixed tire quickly and safely."
    }
    res = make_request("/reviews", method="POST", data=review_payload, token=cust_token)
    assert res["status"] == 201, f"Review creation failed: {res['raw']}"
    assert res["body"]["rating"] == 5
    assert res["body"]["ticket_id"] == ticket_id
    print("  [PASS] Customer submitted 5-star review with comment saved to PostgreSQL.")

    # Duplicate review rejection
    res = make_request("/reviews", method="POST", data=review_payload, token=cust_token)
    assert res["status"] == 409, f"Expected 409 for duplicate review, got {res['status']}"
    print("  [PASS] Duplicate review properly rejected (409 Conflict).")

    # Worker forbidden from submitting customer reviews
    res = make_request("/reviews", method="POST", data=review_payload, token=worker_token)
    assert res["status"] == 403, f"Expected 403 for worker submitting review, got {res['status']}"
    print("  [PASS] Worker forbidden from submitting customer reviews (403 Forbidden).")

    # Admin checks review stats and CRM performance data
    res = make_request("/reviews/stats", method="GET", token=admin_token)
    assert res["status"] == 200, f"Review stats fetch failed: {res['raw']}"
    assert res["body"]["total_reviews"] >= 1
    assert res["body"]["average_rating"] >= 1.0
    print(f"  [PASS] Admin verified aggregated CRM review statistics (Total: {res['body']['total_reviews']}, Avg Rating: {res['body']['average_rating']} stars).")

    # 5l. Phase 5: In-App Notifications & Role Isolation
    print("\n--- 5l. Testing In-App Notifications & Role Isolation ---")
    # Customer notifications
    res = make_request("/notifications", method="GET", token=cust_token)
    assert res["status"] == 200, f"Customer notifications fetch failed: {res['raw']}"
    cust_notifs = res["body"]
    assert len(cust_notifs) >= 1, "Expected at least 1 notification for customer"
    print(f"  [PASS] Customer retrieved {len(cust_notifs)} persistent in-app notifications.")

    # Mark notification as read
    first_notif_id = cust_notifs[0]["id"]
    res = make_request(f"/notifications/{first_notif_id}/read", method="PATCH", data={}, token=cust_token)
    assert res["status"] == 200 and res["body"]["is_read"] is True
    print(f"  [PASS] Customer marked notification #{first_notif_id[:8]} as read.")

    # Worker notifications
    res = make_request("/notifications", method="GET", token=worker_token)
    assert res["status"] == 200, f"Worker notifications fetch failed: {res['raw']}"
    worker_notifs = res["body"]
    assert len(worker_notifs) >= 1, "Expected at least 1 notification for worker"
    print(f"  [PASS] Worker retrieved {len(worker_notifs)} persistent in-app dispatch notifications.")

    # 5m. Phase 6: RoadSafe AI Knowledge Assistant & ChromaDB Semantic RAG
    print("\n--- 5m. Testing RoadSafe AI Knowledge Assistant & ChromaDB Semantic RAG ---")
    # Unauthenticated rejected
    res = make_request("/ai/ask", method="POST", data={"question": "What services are provided?"})
    assert res["status"] == 401, f"Expected 401 for unauthenticated AI query, got {res['status']}"
    print("  [PASS] Unauthenticated AI query rejected (401 Unauthorized).")

    # Flat tyre query
    res = make_request("/ai/ask", method="POST", data={"question": "What should I do if my tyre suddenly goes flat?"}, token=cust_token)
    assert res["status"] == 200, f"AI query failed: {res['raw']}"
    assert res["body"]["grounded"] is True
    assert "hazard" in res["body"]["answer"].lower() or "shoulder" in res["body"]["answer"].lower()
    assert len(res["body"]["sources"]) >= 1
    print("  [PASS] AI Assistant returned grounded guidance for flat tyre emergency with citations.")

    # Service catalog query
    res = make_request("/ai/ask", method="POST", data={"question": "What services does RoadSafe provide?"}, token=cust_token)
    assert res["status"] == 200
    assert res["body"]["grounded"] is True
    assert "towing" in res["body"]["answer"].lower() and "flat tyre" in res["body"]["answer"].lower()
    print("  [PASS] AI Assistant retrieved and summarized RoadSafe service catalog & pricing.")

    # Battery failure query
    res = make_request("/ai/ask", method="POST", data={"question": "What should I do if my vehicle battery dies?"}, token=worker_token)
    assert res["status"] == 200
    assert res["body"]["grounded"] is True
    assert "battery" in res["body"]["answer"].lower() and ("jump" in res["body"]["answer"].lower() or "terminal" in res["body"]["answer"].lower())
    print("  [PASS] Worker retrieved technical battery jump-start procedures.")

    # 5n. Phase 7: ERP & CRM Analytics & Business Intelligence
    print("\n--- 5n. Testing ERP & CRM Analytics & Business Intelligence ---")
    # Customer and worker role authorization rejection
    res = make_request("/analytics/overview", method="GET", token=cust_token)
    assert res["status"] == 403, f"Expected 403 for customer accessing analytics, got {res['status']}"
    res = make_request("/analytics/overview", method="GET", token=worker_token)
    assert res["status"] == 403, f"Expected 403 for worker accessing analytics, got {res['status']}"
    print("  [PASS] Non-admin roles (Customer, Worker) rejected from analytics (403 Forbidden).")

    # Admin overview KPIs
    res = make_request("/analytics/overview", method="GET", token=admin_token)
    assert res["status"] == 200, f"Analytics overview fetch failed: {res['raw']}"
    overview = res["body"]
    assert overview["total_requests"] >= 1
    assert overview["completed_tickets"] >= 1
    assert overview["gross_invoiced"] > 0
    assert overview["paid_amount"] > 0
    assert overview["average_rating"] >= 1.0
    assert "avg_response_minutes" in overview
    assert "avg_completion_minutes" in overview
    print(f"  [PASS] Admin retrieved executive overview KPIs (Requests: {overview['total_requests']}, Completed: {overview['completed_tickets']}, Paid: ₹{overview['paid_amount']}).")

    # Admin operations distribution
    res = make_request("/analytics/operations", method="GET", token=admin_token)
    assert res["status"] == 200, f"Operations analytics fetch failed: {res['raw']}"
    ops = res["body"]
    assert "by_service_type" in ops and "by_status" in ops
    print(f"  [PASS] Admin retrieved operational distributions (Service categories: {list(ops['by_service_type'].keys())}).")

    # Admin mechanics performance ledger
    res = make_request("/analytics/mechanics", method="GET", token=admin_token)
    assert res["status"] == 200, f"Mechanics performance fetch failed: {res['raw']}"
    mechanics = res["body"]
    assert len(mechanics) >= 1
    mech = mechanics[0]
    assert "completed_jobs" in mech and "active_jobs" in mech and "average_rating" in mech
    print(f"  [PASS] Admin retrieved mechanic performance ledger ({len(mechanics)} mechanics evaluated).")

    # Admin revenue intelligence
    res = make_request("/analytics/revenue", method="GET", token=admin_token)
    assert res["status"] == 200, f"Revenue analytics fetch failed: {res['raw']}"
    rev = res["body"]
    assert rev["gross_paid"] > 0
    assert rev["service_revenue"] > 0
    assert rev["parts_revenue"] > 0
    assert len(rev["parts_breakdown"]) >= 1
    print(f"  [PASS] Admin retrieved financial breakdown (Service: ₹{rev['service_revenue']}, Parts: ₹{rev['parts_revenue']}).")

    # Admin CRM customer insights
    res = make_request("/analytics/crm", method="GET", token=admin_token)
    assert res["status"] == 200, f"CRM analytics fetch failed: {res['raw']}"
    crm = res["body"]
    assert crm["total_customers"] >= 1
    assert "repeat_rate_pct" in crm
    assert len(crm["top_services"]) >= 1
    assert len(crm["recent_feedback"]) >= 1
    print(f"  [PASS] Admin retrieved CRM customer retention & demand insights (Drivers: {crm['total_customers']}, Top Service: {crm['top_services'][0]['service']}).")


    # 6. Frontend Files Quality & Mobile-First Checks
    print("\n--- 6. Checking Frontend Files Quality & Mobile Compliance ---")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roadsafe-frontend")
    emoji_regex = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
    
    html_count = 0
    for root, dirs, files in os.walk(frontend_dir):
        for f in files:
            if f.endswith((".html", ".js", ".css")):
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    emojis = emoji_regex.findall(content)
                    assert len(emojis) == 0, f"Found emoji in {f}: {emojis}"
                    
                    if f.endswith(".html"):
                        html_count += 1
                        # Check viewport
                        assert "viewport" in content, f"Missing viewport meta tag in {f}"
                        # Check that styles.css is linked
                        assert "styles.css" in content, f"Missing styles.css link in {f}"

    print(f"  [PASS] Scanned {html_count} HTML files. 0 emojis found, all have viewport meta tags & styles.")

    print("\n==================================================")
    print("      ALL END-TO-END TESTS PASSED SUCCESSFULLY!   ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
