import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from app.models import User
from app.core.config import settings
from app.core import security
from passlib.context import CryptContext

# Setup simpler DB connection
engine = create_async_engine(settings.DATABASE_URL, echo=False)

async def debug_auth():
    async with AsyncSession(engine) as session:
        print("Fetching admin user...")
        query = select(User).where(User.email == "admin@example.com")
        result = await session.execute(query)
        user = result.scalars().first()
        
        if not user:
            print("User admin@example.com not found!")
            return

        print(f"User found: {user.email}")
        print(f"Stored Hash: {user.hashed_password!r}")
        print(f"Hash Length: {len(user.hashed_password)}")
        
        test_password = "admin"
        print(f"Testing password: '{test_password}'")
        
        try:
            # Recreate context to be sure
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            is_valid = pwd_context.verify(test_password, user.hashed_password)
            print(f"Verification result: {is_valid}")
        except Exception as e:
            print(f"Verification FAILED with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_auth())
