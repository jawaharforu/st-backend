"""
Script to seed the database with an admin user.
Run with: python scripts/seed_admin.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.models import User
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin user details - CHANGE THESE!
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"  # Change this!
ADMIN_FULL_NAME = "System Admin"


async def create_admin():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ Admin user '{ADMIN_EMAIL}' already exists!")
            return
        
        # Create admin user
        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_FULL_NAME,
            hashed_password=pwd_context.hash(ADMIN_PASSWORD),
            role="admin"
        )
        
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"   ID: {admin.id}")


if __name__ == "__main__":
    asyncio.run(create_admin())
