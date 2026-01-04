import redis.asyncio as redis
from app.core.config import settings
from typing import Optional

redis_client: Optional[redis.Redis] = None

async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8", 
        decode_responses=True
    )

async def get_redis() -> redis.Redis:
    if redis_client is None:
        await init_redis()
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
