from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select
from app.models import User
from app.core.config import settings
from app.core import security
import asyncio

# Setup simpler DB connection
engine = create_async_engine(settings.DATABASE_URL, echo=False)

async def reset_password():
    async with AsyncSession(engine) as session:
        print("Fetching admin user...")
        query = select(User).where(User.email == "admin@example.com")
        result = await session.execute(query)
        user = result.scalars().first()
        
        if not user:
            print("User admin@example.com not found!")
            return

        print(f"Old Hash: {user.hashed_password}")
        
        # Generate new hash
        new_password = "admin"
        new_hash = security.get_password_hash(new_password)
        print(f"New Hash: {new_hash}")
        
        user.hashed_password = new_hash
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print("Password reset successfully.")
        
        # Verify
        is_valid = security.verify_password(new_password, user.hashed_password)
        print(f"Verification Check: {is_valid}")

if __name__ == "__main__":
    asyncio.run(reset_password())
