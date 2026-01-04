import asyncio
from sqlalchemy import text
from app.api.deps import get_db
from app.models import Command
from app.core.db import engine

async def fix_schema():
    async with engine.begin() as conn:
        print("Checking/Adding params column to command table...")
        try:
            # Attempt to add the column. If it exists, it might error or we can check first.
            # Postgres: ALTER TABLE command ADD COLUMN IF NOT EXISTS params JSONB;
            # SQLModel/SA uses JSON, usually maps to JSON or JSONB in PG.
            await conn.execute(text("ALTER TABLE command ADD COLUMN IF NOT EXISTS params JSON;"))
            print("Column 'params' added or already exists.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())
