from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.redis import get_redis
import json
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/farms/{farm_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    farm_id: str,
    token: str = Query(...)
):
    # TODO: Validate token (auth)
    # For now, minimal validation logic or call get_current_user via dependency?
    # WebSockets don't support headers easily in standard JS API, usually query param.
    # verification logic here:
    
    await websocket.accept()
    redis = await get_redis()
    pubsub = redis.pubsub()
    
    channel = f"telemetry:{farm_id}"
    await pubsub.subscribe(channel)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.01) # fast loop
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from {channel}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
