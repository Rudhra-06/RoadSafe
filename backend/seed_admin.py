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


if __name__ == "__main__":
    asyncio.run(seed_admin())
