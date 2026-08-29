"""
Seed knowledge documents for RoadSafe AI Assistant.
Contains verified guidance on roadside emergencies, service catalog, safety protocols, and FAQs.
"""

KNOWLEDGE_DOCUMENTS = [
    {
        "id": "doc_flat_tyre",
        "title": "Flat Tyre Emergency Guidance & Safety",
        "category": "emergency",
        "content": (
            "If your vehicle experiences a flat tyre while driving:\n"
            "1. Turn on your hazard lights immediately to warn surrounding traffic.\n"
            "2. Gently reduce speed and pull over safely to the far left shoulder or curb away from traffic.\n"
            "3. Shift to Park (or 1st gear for manual) and engage the handbrake firmly.\n"
            "4. Turn wheels away from the road if parked on an incline.\n"
            "5. If on a high-speed highway or in unsafe traffic, stay inside the vehicle with your seatbelt fastened or stand well behind the safety barrier.\n"
            "6. Request RoadSafe Flat Tyre Assistance (₹299 base price). A certified roadside technician will arrive on-site to replace your wheel with your spare or perform a puncture repair."
        ),
        "tags": ["flat tyre", "puncture", "tyre", "wheel", "spare", "rubber", "stepney"]
    },
    {
        "id": "doc_battery",
        "title": "Battery Failure & Jump-Start Guidance",
        "category": "emergency",
        "content": (
            "If your car battery dies or fails to start:\n"
            "1. Common symptoms include rapid clicking sounds when turning the key, dim dashboard lights, or electrical failure.\n"
            "2. Never attempt to jump-start a battery that is leaking, visibly swollen, or damaged.\n"
            "3. Ensure both vehicles are turned off before connecting jumper cables (Red to Positive +, Black to Negative - or unpainted chassis ground).\n"
            "4. Request RoadSafe Battery Assistance (₹349 base price). Our mobile technicians carry portable high-capacity jump-starters, voltage diagnostic tools, and replacement battery terminal clamps."
        ),
        "tags": ["battery", "jump start", "dead battery", "no crank", "alternator", "terminal", "electrical"]
    },
    {
        "id": "doc_fuel",
        "title": "Fuel Exhaustion & Emergency Delivery",
        "category": "emergency",
        "content": (
            "If your vehicle runs out of petrol or diesel:\n"
            "1. Safely maneuver to the shoulder before the engine stalls completely.\n"
            "2. Turn on hazard warning lights.\n"
            "3. Avoid repeatedly cranking an empty fuel system as this can overheat and damage the in-tank fuel pump.\n"
            "4. Request RoadSafe Fuel Assistance (₹199 base price). We deliver up to 5 litres of petrol or diesel directly to your GPS coordinates to get you safely to the nearest filling station."
        ),
        "tags": ["fuel", "petrol", "diesel", "empty tank", "fuel delivery", "refuel", "gas"]
    },
    {
        "id": "doc_engine",
        "title": "Engine Breakdown & Overheating Precautions",
        "category": "emergency",
        "content": (
            "If your engine overheats or suffers a mechanical breakdown:\n"
            "1. If steam is coming from the hood or the temperature gauge is in the red zone, switch off the air conditioner and pull over immediately in a safe spot.\n"
            "2. Turn off the ignition to stop engine damage.\n"
            "3. NEVER open the radiator cap or coolant expansion tank while the engine is hot—pressurized boiling coolant can cause severe burns.\n"
            "4. Allow the engine to cool down for at least 20–30 minutes.\n"
            "5. Request RoadSafe Mechanical Breakdown Assistance (₹499 base price) for on-site diagnostic scan and minor repairs, or Towing if severe."
        ),
        "tags": ["engine", "breakdown", "overheating", "steam", "radiator", "coolant", "smoke", "mechanical"]
    },
    {
        "id": "doc_towing",
        "title": "Towing Service & Safety Protocols",
        "category": "towing",
        "content": (
            "When to request Towing Assistance:\n"
            "1. Major mechanical failures, locked transmissions, severe collision damage, or seized engines require flatbed towing.\n"
            "2. Before towing, ensure the vehicle steering is unlocked and gear is in Neutral.\n"
            "3. RoadSafe Towing Assistance (₹799 base price) provides GPS-tracked flatbed and wheel-lift tow trucks with safe vehicle securing up to 10 km to the nearest garage or your preferred workshop."
        ),
        "tags": ["towing", "tow truck", "flatbed", "accident", "recovery", "workshop", "garage"]
    },
    {
        "id": "doc_safety",
        "title": "General Highway & Vehicle Breakdown Safety Precautions",
        "category": "safety",
        "content": (
            "Essential roadside safety rules during any breakdown:\n"
            "1. Park as far left from moving traffic as possible on the hard shoulder or service lane.\n"
            "2. Activate emergency hazard flashers immediately.\n"
            "3. Place a reflective warning triangle 50 meters behind your vehicle on standard roads, or 100 meters on highways.\n"
            "4. Wear a reflective safety vest if stepping out at night.\n"
            "5. Passengers should exit via the curb-side doors (left side) and wait behind highway guardrails rather than sitting in the vehicle in high-speed zones."
        ),
        "tags": ["safety", "highway", "hazard lights", "warning triangle", "precautions", "emergency"]
    },
    {
        "id": "doc_catalog",
        "title": "RoadSafe Complete Service Catalog & Pricing",
        "category": "services",
        "content": (
            "RoadSafe provides 24/7 on-demand roadside assistance across urban and highway corridors:\n"
            "- Towing Assistance: ₹799 (Includes tow up to 10km, GPS tracked tow truck)\n"
            "- Flat Tyre Assistance: ₹299 (On-site wheel change or puncture patch)\n"
            "- Battery Assistance: ₹349 (Jump-start service, battery health check, terminal cleaning)\n"
            "- Fuel Assistance: ₹199 (Emergency delivery of up to 5L petrol/diesel)\n"
            "- Mechanical Breakdown: ₹499 (On-site diagnosis, minor repairs up to 1 hour)\n"
            "- Lockout Assistance: ₹249 (Non-destructive entry, key retrieval)\n"
            "- General Roadside Assistance: ₹199 (Safety assessment, basic troubleshooting)"
        ),
        "tags": ["services", "pricing", "cost", "rates", "catalog", "how much", "fees"]
    },
    {
        "id": "doc_faq",
        "title": "RoadSafe Frequently Asked Questions & Operational Help",
        "category": "faq",
        "content": (
            "Frequently Asked Questions:\n"
            "- How does dispatch work? When you request assistance, RoadSafe GPS automatically matches the nearest verified technician within 10 km.\n"
            "- How can I track my technician? Once assigned, live real-time GPS telemetry shows the technician's route and ETA on your tracking screen.\n"
            "- What payment methods are accepted? We accept digital payments via Razorpay (UPI, Credit/Debit Cards, NetBanking) and transparent itemized invoices.\n"
            "- Are technicians certified? Yes, all RoadSafe responders undergo identity and qualification verification before receiving job dispatches."
        ),
        "tags": ["faq", "help", "dispatch", "payment", "tracking", "eta", "time", "technician"]
    },
    {
        "id": "doc_auto_care_shops",
        "title": "Auto Care Shops & Partner Workshop Network",
        "category": "workshops",
        "content": (
            "RoadSafe maintains a 24/7 active verified network of partner Auto Care Shops, certified garages, and mobile mechanic units:\n"
            "1. Network Status: All partnered Auto Care Shops and mobile responder hubs operate 24/7 on-call for roadside assistance, vehicle diagnostic scans, and emergency mechanical overhauls.\n"
            "2. Dispatch & Proximity: When a driver requests assistance or towing, RoadSafe's location-aware dispatch engine routes the closest active auto care responder or directs towing to the nearest certified partner garage within the service radius.\n"
            "3. Certified Standards: Partner shops provide genuine parts with itemized transparent billing, guaranteed turnaround times, and verified warranty coverage.\n"
            "4. Finding an Active Shop: Drivers and operators can view active provider listings with live availability directly in the RoadSafe app under the Providers directory or by initiating a request."
        ),
        "tags": ["auto care", "shop", "shops", "active", "garage", "workshop", "partner", "mechanic", "mechanics", "centers", "service station", "store"]
    },
    {
        "id": "doc_responder_network",
        "title": "Responder On-Duty & Active Availability Protocols",
        "category": "operations",
        "content": (
            "RoadSafe active responder operations & duty guidelines:\n"
            "1. On-Duty Availability: Responders (car mechanics, bike mechanics, tow operators, paramedics) toggle their live availability to 'Active' via the worker dashboard to receive automated dispatches.\n"
            "2. GPS Telemetry: Active responders transmit real-time GPS coordinates via browser/mobile geolocation so the dispatch engine can calculate accurate ETAs and nearest-responder assignment.\n"
            "3. Auto Care Dispatch: Requests are matched based on required skill (e.g. Car Mechanic, Towing, Electrical) and physical distance to ensure fast emergency response times."
        ),
        "tags": ["responder", "active", "online", "duty", "availability", "auto care", "operator", "mechanic", "dispatch"]
    }
]

