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

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin"
ADMIN_FULL_NAME = "RoadSafe Admin"
ADMIN_PHONE = "0000000000"


async def seed_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == ADMIN_EMAIL))
        existing = result.scalars().first()
        if existing:
            print(f"[seed] Admin '{ADMIN_EMAIL}' already exists — skipping.")
            return
        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            full_name=ADMIN_FULL_NAME,
            phone_number=ADMIN_PHONE,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[seed] Admin '{ADMIN_EMAIL}' created successfully.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
