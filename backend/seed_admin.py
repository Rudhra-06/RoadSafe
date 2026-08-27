import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.utils.enums import UserRole
from app.core.security import get_password_hash

async def seed_admin():
    email = input("Admin Email: ")
    password = input("Admin Password: ")
    full_name = input("Admin Full Name: ")

    async with SessionLocal() as db:
        from sqlalchemy.future import select
        result = await db.execute(select(User).filter(User.email == email))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"User with email {email} already exists!")
            return
            
        hashed_pwd = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_pwd,
            full_name=full_name,
            phone_number="0000000000",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        print(f"Admin user {email} created successfully!")

if __name__ == "__main__":
    print("--- RoadSafe ERP Admin Seeder ---")
    asyncio.run(seed_admin())
