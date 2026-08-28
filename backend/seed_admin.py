"""
Auto-seeds the admin account on startup.
Run directly:  python seed_admin.py
Or called from lifespan in main.py.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.utils.enums import UserRole
from app.core.security import get_password_hash

import json
from app.models.service_catalog import Service

ADMINS_TO_SEED = [
    {
        "email": "admin@roadsafe.com",
        "password": "AdminPass123!",
        "full_name": "RoadSafe Admin (Test)",
        "phone_number": "0000000000",
    },
    {
        "email": "admin@gmail.com",
        "password": "admin",
        "full_name": "RoadSafe Default Admin",
        "phone_number": "1111111111",
    }
]

SERVICES_TO_SEED = [
    {
        "name": "Flat Tyre",
        "description": "On-site tyre change, puncture repair, and tyre pressure check by certified technicians.",
        "category": "Tyre",
        "base_price": 299.00,
        "estimated_duration_minutes": 20,
        "features": ["Spare tyre replacement", "Puncture repair", "Pressure check"],
        "included_items": ["Technician labour", "Puncture kit"],
        "possible_parts": ["Tyre tube", "Valve stem", "Wheel nut"],
        "is_active": True,
    },
    {
        "name": "Battery Assistance",
        "description": "Jump-start assistance or on-site battery testing and replacement.",
        "category": "Battery",
        "base_price": 349.00,
        "estimated_duration_minutes": 15,
        "features": ["Jump-start service", "Battery health test", "Terminal cleaning"],
        "included_items": ["Labour", "Heavy-duty jump cables"],
        "possible_parts": ["12V Car Battery", "Battery Clamps"],
        "is_active": True,
    },
    {
        "name": "Fuel Delivery",
        "description": "Emergency fuel delivery (petrol/diesel) delivered directly to your roadside location.",
        "category": "Fuel",
        "base_price": 199.00,
        "estimated_duration_minutes": 25,
        "features": ["Emergency petrol/diesel delivery", "Safe dispensing", "Fast dispatch"],
        "included_items": ["Delivery fee (up to 5L fuel available)"],
        "possible_parts": [],
        "is_active": True,
    },
    {
        "name": "Engine Breakdown",
        "description": "Comprehensive on-site engine diagnostics, overheating checks, and mechanical repair.",
        "category": "Mechanical",
        "base_price": 499.00,
        "estimated_duration_minutes": 45,
        "features": ["Engine diagnostics", "Cooling system check", "Minor mechanical fix"],
        "included_items": ["First 45 mins labour", "Diagnostic scan"],
        "possible_parts": ["Fan belt", "Spark plugs", "Radiator hose", "Fuses"],
        "is_active": True,
    },
    {
        "name": "Towing",
        "description": "Safe flatbed and wheel-lift vehicle towing to your preferred repair facility.",
        "category": "Towing",
        "base_price": 799.00,
        "estimated_duration_minutes": 30,
        "features": ["Flatbed towing", "Safe vehicle loading", "GPS real-time tracking"],
        "included_items": ["Towing up to 10km", "Loading/unloading"],
        "possible_parts": [],
        "is_active": True,
    },
    {
        "name": "General Roadside Assistance",
        "description": "General inspections, minor electrical troubleshooting, lockout assistance, and quick roadside fixes.",
        "category": "General",
        "base_price": 399.00,
        "estimated_duration_minutes": 30,
        "features": ["Safety check", "Minor electrical fix", "General roadside diagnosis"],
        "included_items": ["30 mins technician assistance", "Basic roadside tools"],
        "possible_parts": ["Fuses", "Relays", "Bulbs"],
        "is_active": True,
    }
]

PARTS_TO_SEED = [
    {
        "name": "Spark Plug Set (4pcs)",
        "part_number": "SP-4X-001",
        "description": "Standard high-performance spark plug set for petrol engines.",
        "unit_price": 450.00,
        "stock_quantity": 40,
        "is_active": True,
    },
    {
        "name": "Battery Terminal Clamp",
        "part_number": "BTC-12V-002",
        "description": "Heavy duty brass battery terminal clamp.",
        "unit_price": 120.00,
        "stock_quantity": 50,
        "is_active": True,
    },
    {
        "name": "Engine Fan Belt",
        "part_number": "FB-ENG-003",
        "description": "Reinforced serpentine engine fan belt.",
        "unit_price": 350.00,
        "stock_quantity": 25,
        "is_active": True,
    },
    {
        "name": "Radiator Hose",
        "part_number": "RH-COOL-004",
        "description": "Heat resistant flexible cooling radiator hose.",
        "unit_price": 280.00,
        "stock_quantity": 20,
        "is_active": True,
    },
    {
        "name": "Tyre Tube (Standard)",
        "part_number": "TT-STD-005",
        "description": "Durable inner tube for car and light commercial tyres.",
        "unit_price": 300.00,
        "stock_quantity": 30,
        "is_active": True,
    },
    {
        "name": "Automotive Fuse 15A",
        "part_number": "FUSE-15A-006",
        "description": "15 Amp standard blade automotive fuse.",
        "unit_price": 30.00,
        "stock_quantity": 100,
        "is_active": True,
    }
]

from app.models.parts_catalog import Part

async def seed_parts():
    async with AsyncSessionLocal() as db:
        for p_data in PARTS_TO_SEED:
            result = await db.execute(select(Part).filter(Part.name == p_data["name"]))
            existing = result.scalars().first()
            if existing:
                print(f"[seed] Part '{p_data['name']}' already exists — skipping.")
                continue

            part = Part(
                name=p_data["name"],
                part_number=p_data["part_number"],
                description=p_data["description"],
                unit_price=p_data["unit_price"],
                stock_quantity=p_data["stock_quantity"],
                is_active=p_data["is_active"],
            )
            db.add(part)
            await db.commit()
            print(f"[seed] Part '{p_data['name']}' seeded successfully.")


async def seed_admin():
    async with AsyncSessionLocal() as db:
        for admin_data in ADMINS_TO_SEED:
            result = await db.execute(select(User).filter(User.email == admin_data["email"]))
            existing = result.scalars().first()
            if existing:
                print(f"[seed] Admin '{admin_data['email']}' already exists — skipping.")
                continue
            
            admin = User(
                email=admin_data["email"],
                hashed_password=get_password_hash(admin_data["password"]),
                full_name=admin_data["full_name"],
                phone_number=admin_data["phone_number"],
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            await db.commit()
            print(f"[seed] Admin '{admin_data['email']}' created successfully.")


async def seed_services():
    async with AsyncSessionLocal() as db:
        for s_data in SERVICES_TO_SEED:
            result = await db.execute(select(Service).filter(Service.name == s_data["name"]))
            existing = result.scalars().first()
            if existing:
                print(f"[seed] Service '{s_data['name']}' already exists — skipping.")
                continue

            service = Service(
                name=s_data["name"],
                description=s_data["description"],
                category=s_data["category"],
                base_price=s_data["base_price"],
                estimated_duration_minutes=s_data["estimated_duration_minutes"],
                features=json.dumps(s_data["features"]),
                included_items=json.dumps(s_data["included_items"]),
                possible_parts=json.dumps(s_data["possible_parts"]),
                is_active=s_data["is_active"],
            )
            db.add(service)
            await db.commit()
            print(f"[seed] Service '{s_data['name']}' seeded successfully.")


async def seed_all():
    await seed_admin()
    await seed_services()
    await seed_parts()


if __name__ == "__main__":
    asyncio.run(seed_all())
